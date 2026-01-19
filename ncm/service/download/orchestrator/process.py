"""下载编排器的流程模块。

本模块将原先位于 core.py 中的流程逻辑独立出来，形成职责清晰的结构：
－ 作业任务准备；
－ 批次处理（同音质复制优化或创建待下载任务）；
－ 批次调度与等待；
－ 歌单曲目获取及带退避的批量详情拉取与作业内去重。
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import Dict, Any, List, Tuple

from ncm.server.routers.music import PlaylistController
from ncm.server.routers.music.song import SongController
from ncm.core.logging import get_logger
from ncm.infrastructure.db.async_session import get_uow_factory
from ncm.infrastructure.db.models.download_job import DownloadJob
from ncm.infrastructure.db.models.download_task import DownloadTask
from ncm.infrastructure.db.repositories.async_download_job_repo import (
    AsyncDownloadJobRepository,
)
from ncm.infrastructure.db.repositories.async_download_task_repo import (
    AsyncDownloadTaskRepository,
)
from ncm.service.download.models import get_task_cache_registry
from ncm.service.download.orchestrator import DownloadOrchestrator
from ncm.service.download.service import AsyncJobService
from ncm.service.download.storage.manager import StorageManager
from ncm.infrastructure.utils.time import UTC_CLOCK

logger = get_logger(__name__)


class DownloadProcess:
    """下载流程服务；与核心编排器解耦，负责作业扫描、任务准备、复制优化与批次调度。"""

    def __init__(self, orchestrator: DownloadOrchestrator):
        """初始化流程服务；自建数据库与控制器依赖，并持有编排器以执行下载工作流。"""
        self.orch = orchestrator
        self.uow_factory = get_uow_factory()  # 数据库单元工厂；用于管理事务与会话
        self.task_repo = AsyncDownloadTaskRepository()  # 任务仓库；读写下载任务
        self.job_repo = AsyncDownloadJobRepository()  # 作业仓库；读写下载作业
        self.job_service = AsyncJobService()  # 作业服务；封装状态流转
        self.storage_manager = StorageManager()  # 存储管理器；生成最终路径与文件移动
        self._song_controller = None  # 懒加载歌曲控制器实例
        self._playlist_controller = None  # 懒加载歌单控制器实例
        self._copy_locks: dict[str, asyncio.Lock] = (
            {}
        )  # 针对每个 music_id 的复制锁，避免并发复制冲突
        self._run_lock = asyncio.Lock()
        self._status: Dict[str, Any] = {
            "running": False,
            "started_at": None,
            "finished_at": None,
            "processed_jobs": 0,
            "submitted_tasks": 0,
            # "skipped_existing": 0,
            "skipped_in_library": 0,
            "failed_jobs": 0,
            "current_job_id": None,
            "current_batch_index": 0,
        }
        self._running_task: asyncio.Task | None = None

    def get_status(self) -> Dict[str, Any]:
        return dict(self._status)

    def is_running(self) -> bool:
        return self._status.get("running", False)

    async def start(self, batch_size: int = 10) -> bool:
        if self.is_running():
            return False
        self._running_task = asyncio.create_task(self.run(batch_size=batch_size))
        return True

    @property
    def song_controller(self):
        """获取歌曲控制器；按需初始化以减少启动开销。"""
        if self._song_controller is None:
            self._song_controller = SongController()
        return self._song_controller

    @property
    def playlist_controller(self):
        """获取歌单控制器；按需初始化以减少启动开销。"""
        if self._playlist_controller is None:
            self._playlist_controller = PlaylistController()
        return self._playlist_controller

    async def run(self, batch_size: int = 10) -> Dict[str, Any]:
        if self._run_lock.locked():
            return self.get_status()

        async with self._run_lock:
            await self._init_run_status()

            jobs = await self.job_service.get_job_all_enabled()
            if not jobs:
                return await self._finalize_run()

            for job in jobs:
                try:
                    await self._process_single_job(job, batch_size)
                except Exception as e:
                    await self._handle_job_exception(job, e)

            return await self._finalize_run()

    async def _init_run_status(self) -> None:
        """初始化运行状态。"""
        self._status.update(
            {
                "running": True,
                "started_at": UTC_CLOCK.now().isoformat(),
                "finished_at": None,
                "processed_jobs": 0,
                "submitted_tasks": 0,
                "skipped_in_library": 0,
                "failed_jobs": 0,
                "current_job_id": None,
                "current_batch_index": 0,
            }
        )

    async def _finalize_run(self) -> Dict[str, Any]:
        """收尾运行状态并返回快照。"""
        self._status.update(
            {
                "running": False,
                "finished_at": UTC_CLOCK.now().isoformat(),
                "current_job_id": None,
                "current_batch_index": 0,
            }
        )
        return self.get_status()

    def _update_success_stats(self, submitted_count: int) -> None:
        """更新成功统计数据。"""
        self._status["processed_jobs"] = int(self._status.get("processed_jobs", 0)) + 1
        self._status["submitted_tasks"] = (
            int(self._status.get("submitted_tasks", 0)) + submitted_count
        )

    async def _process_single_job(
        self, job: DownloadJob, batch_size: int
    ) -> None:
        """处理单个作业的核心流程。"""
        self._status["current_job_id"] = job.id
        self._status["current_batch_index"] = 0
        logger.info(f"开始扫描{job.get_job_name}")
        # logger.debug(f"--- Starting Job {job.id} ---")
        await self.job_service.set_job_status_scanning(job.id)

        if job.job_type == "playlist" or job.source_type == "playlist":
            tasks, failed_ids = await self._prepare_playlist_tasks(job)
        else:
            raise ValueError(f"Unsupported job type: {job.job_type}")

        logger.info(f"扫描{job.get_job_name}完成，获取到 {len(tasks)} 首新歌曲")  
        if len(tasks) == 0:
            return
        submitted_count = await self._handle_batches(job, tasks, batch_size)
        # logger.debug(f"--- Finished Job {job.id} ---")
 
        await self.job_service.set_job_status_completed(job.id)
        self._update_success_stats(submitted_count)
        logger.info(f"{job.get_job_name}完成，成功下载 {submitted_count} 首新歌曲")

        if failed_ids:
            logger.warning(
                f"Job {job.id}: {len(failed_ids)} tracks failed to fetch details."
            )

    async def _handle_job_exception(
        self, job: DownloadJob, exc: Exception
    ) -> None:
        """统一处理作业异常。"""
        logger.exception(f"Job {job.id} failed: {exc}")
        await self.job_service.set_job_status_failed(job.id)
        self._status["failed_jobs"] = int(self._status.get("failed_jobs", 0)) + 1

    async def _prepare_playlist_tasks(
        self, job: DownloadJob
    ) -> Tuple[List[DownloadTask], List[str]]:
        """针对歌单作业准备 DownloadTask 列表并预注入 song_detail 缓存。"""
        fetch_result = await self._fetch_playlist_tracks(job.id, job.source_id)

        detailed_tracks = fetch_result.get("tracks", [])
        failed_ids = fetch_result.get("failed_ids", [])

        detail_map: Dict[str, dict] = {}
        for track in detailed_tracks:
            music_id = str(track.get("id"))
            if not music_id:
                continue
            detail_map[music_id] = track

        async with self.uow_factory() as uow:
            tasks = await self.task_repo.create_batch_ids_and_get_pending_music(
                uow.session,
                job.id,
                fetch_result.get("effective_ids", []),
            )

        registry = get_task_cache_registry()
        for task in tasks:
            cache = await registry.get_or_create(task.id, task.music_id)
            cache.song_detail = detail_map.get(task.music_id)

        return tasks, failed_ids

    async def _handle_batches(
        self,
        job: DownloadJob,
        tasks: List[DownloadTask],
        batch_size: int,
    ) -> int:
        """执行批次调度；针对已存在的 DownloadTask 列表按顺序分批调度。"""
        submitted_ids: List[int] = []
        batch_index = 0

        logger.info(f"开始分批下载{job.get_job_name}，每批大小: {batch_size}")
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i : i + batch_size]
            if not batch:
                continue
            batch_index += 1
            self._status["current_batch_index"] = batch_index
            # logger.debug(
            #     f"Starting batch {batch_index} for job {job.id} with {len(batch)} tasks"
            # )
            logger.info(
                f"开始下载{job.get_job_name}的第 {batch_index} 批次"
            )
            await self._dispatch_and_wait_batch(job, batch)
            submitted_ids.extend([t.id for t in batch])

        return len(submitted_ids)

    async def _try_copy_existing(self, job: DownloadJob, data: dict) -> int | None:
        """尝试基于同音质来源任务进行文件复制并直接完成当前任务；失败则返回 None。"""
        source_task: DownloadTask | None = None  # 来源任务对象（若存在且音质匹配）
        async with self.uow_factory() as uow:
            source_task = await self.task_repo.find_completed_by_music_and_quality(
                uow.session, data["music_id"], job.target_quality,
            )
            if not source_task or not source_task.file_path:
                return None
        lock = self._copy_locks.setdefault(
            data["music_id"], asyncio.Lock()
        )  # 针对 music_id 的复制锁
        async with lock:
            async with self.uow_factory() as uow:
                try:
                    new_task = await self.task_repo.create(
                        uow.session,
                        music_id=data["music_id"],
                        job_id=data["job_id"],
                        music_title=data.get("music_title"),
                        music_artist=data.get("music_artist"),
                        music_album=data.get("music_album"),
                        quality=source_task.quality,
                        file_format=source_task.file_format,
                    )

                    job_obj = await self.job_repo.get_by_id(uow.session, job.id)
                    target_path = self.storage_manager._generate_final_path(
                        new_task, job_obj
                    )
                    
                    # 确保目标目录存在
                    from ncm.infrastructure.utils.path import prepare_path
                    prepare_path(target_path.parent)
                    
                    shutil.copy2(source_task.file_path, str(target_path))  # 复制文件
                    await self.task_repo.update(
                        uow.session,
                        new_task.id,
                        status="completed",
                        file_path=str(target_path),
                        file_name=target_path.name,
                        progress_flags=source_task.progress_flags,
                        error_message=json.dumps(
                            {
                                "copied_from": {
                                    "job_id": source_task.job_id,
                                    "task_id": source_task.id,
                                    "file_path": source_task.file_path,
                                }
                            },
                            ensure_ascii=False,
                        ),
                    )
                    return new_task.id
                except Exception as ce:
                    # 回滚由 UnitOfWork 处理；确保删除已复制的文件
                    try:
                        if "target_path" in locals() and os.path.exists(
                                str(target_path)
                        ):
                            os.remove(str(target_path))  # 清理失败复制的残留目标文件
                    except Exception:
                        pass
                    logger.warning(
                        f"Copy optimization failed for music {data['music_id']}: {ce}"
                    )
                    return None

    async def _dispatch_and_wait_batch(
            self, job: DownloadJob, created: List[DownloadTask]
    ) -> None:
        """调度当前批次的下载工作流并等待所有子流程完成；收集异常并记录日志。"""
        # 调度执行工作流
        batch_futures: List[asyncio.Task] = []  # 子任务 Future 列表
        for task in created:
            future = asyncio.create_task(
                self.orch._execute_download_workflow(task.id, job.target_quality)
            )
            self.orch.task_manager.register_task(task.id, future)
            batch_futures.append(future)

        # 等待当前批次所有任务完成（包括所有子流程）
        if batch_futures:
            done = await asyncio.gather(*batch_futures, return_exceptions=True)
            # 记录异常但不影响后续批次
            for idx, res in enumerate(done):
                task = created[idx]
                if isinstance(res, Exception):
                    logger.warning(f"{job.source_type}\"{job.job_name}\" 批次任务 {task.id} 引发异常: {res}")

    async def _fetch_playlist_tracks(
            self, job_id: int, playlist_id: str, max_retries: int = 3
    ) -> dict:
        """获取歌单曲目 ID 并批量拉取歌曲详情；包含重试与歌曲ID去重。"""
        delay = 1.0  # 初始重试延迟秒数
        all_ids: List[str] = []  # 歌单中的所有曲目 ID（去重前）
        for attempt in range(max_retries):
            try:
                resp = await self.playlist_controller.playlist_detail(id=playlist_id)
                if getattr(resp, "success", False):
                    body = getattr(resp, "body", {}) or {}
                    playlist_data = body.get("playlist") or {}
                    track_ids_raw = playlist_data.get("trackIds") or []
                    ids: List[str] = []  # 规范化后的曲目 ID 列表
                    for item in track_ids_raw:
                        if isinstance(item, dict) and "id" in item:
                            ids.append(str(item["id"]))
                        elif isinstance(item, (int, str)):
                            ids.append(str(item))
                    all_ids = list(dict.fromkeys(ids))  # 去重保序
                    break
                status = getattr(resp, "status", 0) or 0
                if status in (429, 503):
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 8.0)
                    continue
                    # 触发降级路径；返回空结果以避免阻塞
                return {
                    "tracks": [],
                    "effective_ids": [],
                    "failed_ids": [],
                    # "skipped_existing_ids": [],
                }
            except Exception as e:
                logger.warning(
                    f"Fetch playlist detail failed for {playlist_id} (attempt {attempt + 1}): {e}"
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)

        # 上述代码会取到all_ids，已知歌单的tracks包含歌单完整id列表
        # 作业内去重：排除已存在任务，仅保留 pending 状态
        async with self.uow_factory() as uow:
            pending_tasks = await self.task_repo.create_batch_ids_and_get_pending_music(
                uow.session, job_id, all_ids
            )
            effective_ids = [t.music_id for t in pending_tasks]

        # existing_ids: set[str] = set()  # 当前作业已存在任务的 music_id 集合
        # async with self.uow_factory() as uow:
        #     existing_tasks = await self.task_repo.list_by_job(uow.session, job_id)
        #     for t in existing_tasks:
        #         if t.music_id:
        #             existing_ids.add(str(t.music_id))
        #
        # effective_ids = [
        #     mid for mid in all_ids if mid not in existing_ids
        # ]  # 作业内新任务的歌曲 ID
        # skipped_existing_ids = [
        #     mid for mid in all_ids if mid in existing_ids
        # ]  # 已存在任务的歌曲 ID

        detailed_tracks: List[dict] = []  # 拉取到的歌曲详情
        failed_ids: List[str] = []  # 拉取失败的歌曲 ID
        chunk_size = 300  # 详情拉取的分块大小；避免接口长度与频率限制
        for i in range(0, len(effective_ids), chunk_size):
            chunk = effective_ids[i: i + chunk_size]
            try:
                resp = await self.song_controller.song_detail(ids=",".join(chunk))
                if getattr(resp, "success", False):
                    body = getattr(resp, "body", {}) or {}
                    songs = body.get("songs") or []
                    detailed_tracks.extend(songs)
                else:
                    failed_ids.extend(chunk)
            except Exception as e:
                logger.warning(
                    f"Fetch song details failed for chunk starting {chunk[0]}: {e}"
                )
                failed_ids.extend(chunk)
        return {
            "tracks": detailed_tracks,
            "effective_ids": effective_ids,
            "failed_ids": failed_ids,
            # "skipped_existing_ids": skipped_existing_ids,
        }

    async def cleanup(self):
        """Cleanup process resources."""
        if self._running_task and not self._running_task.done():
            self._running_task.cancel()
            try:
                await self._running_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Error during process task cancellation: {e}")
            logger.info("DownloadProcess task cancelled")

        # Dispose uow_factory to release DB resources
        if hasattr(self.uow_factory, "dispose") and callable(self.uow_factory.dispose):
            try:
                await self.uow_factory.dispose()
                logger.debug("DownloadProcess uow_factory disposed")
            except Exception as e:
                logger.warning(f"Error disposing DownloadProcess uow_factory: {e}")
