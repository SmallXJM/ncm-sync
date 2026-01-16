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

from ncm.api.ncm.music.playlist import PlaylistController
from ncm.api.ncm.music.song import SongController
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
from ncm.service.download.service import AsyncJobService
from ncm.service.download.storage.manager import StorageManager
from ncm.infrastructure.utils.time import UTC_CLOCK

logger = get_logger(__name__)


class DownloadProcess:
    """下载流程服务；与核心编排器解耦，负责作业扫描、任务准备、复制优化与批次调度。"""

    def __init__(self, orchestrator):
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
            "skipped_existing": 0,
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
        """
        处理所有启用的下载作业

        Args:
            batch_size: 每批提交的任务数量

        Returns:
            当前状态快照（仅返回运行锁范围内的关键参数）
        """
        if self._run_lock.locked():
            return self.get_status()
        async with self._run_lock:
            self._status.update(
                {
                    "running": True,
                    "started_at": UTC_CLOCK.now().isoformat(),
                    "finished_at": None,
                    "processed_jobs": 0,
                    "submitted_tasks": 0,
                    "skipped_existing": 0,
                    "skipped_in_library": 0,
                    "failed_jobs": 0,
                    "current_job_id": None,
                    "current_batch_index": 0,
                }
            )
            # 获取所有启用的下载作业
            jobs = await self.job_service.get_job_all_enabled()
            if not jobs:
                self._status.update(
                    {"running": False, "finished_at": UTC_CLOCK.now().isoformat()}
                )
                return self.get_status()
            for job in jobs:
                try:
                    # 标记作业进入扫描状态
                    await self.job_service.set_job_status_scanning(job.id)

                    self._status["current_job_id"] = job.id
                    self._status["current_batch_index"] = 0

                    # 根据作业类型选择曲目获取策略；目前仅支持歌单类型
                    if job.job_type == "playlist" or job.source_type == "playlist":
                        # 获取歌单曲目详情（带重试与作业内去重）
                        fetch_result = await self._fetch_playlist_tracks(
                            job.id, job.source_id
                        )
                    else:
                        await self.job_service.set_job_status_failed(job.id)
                        self._status["failed_jobs"] = (
                            int(self._status.get("failed_jobs", 0)) + 1
                        )
                        continue

                    # 任务准备阶段前置执行同音质复制优化；返回待下载任务与已复制任务
                    tasks_data, detail_map, failed_ids, skipped_existing, copied_ids = (
                        await self._prepare_job_tasks(job, fetch_result)
                    )
                    submitted_count = await self._handle_batches(
                        job, tasks_data, detail_map, batch_size
                    )

                    # 更新作业状态为已完成
                    await self.job_service.set_job_status_completed(job.id)
                    self._status["processed_jobs"] = (
                        int(self._status.get("processed_jobs", 0)) + 1
                    )
                    self._status["submitted_tasks"] = (
                        int(self._status.get("submitted_tasks", 0))
                        + submitted_count
                        + len(copied_ids)
                    )
                    self._status["skipped_existing"] = int(
                        self._status.get("skipped_existing", 0)
                    ) + len(skipped_existing)

                    if failed_ids:
                        logger.warning(
                            f"Playlist fetch detail failed for some ids in job {job.id}: {len(failed_ids)}"
                        )

                except Exception as e:
                    logger.exception(f"Job processing failed for job {job.id}: {e}")
                    await self.job_service.set_job_status_failed(job.id)
                    self._status["failed_jobs"] = (
                        int(self._status.get("failed_jobs", 0)) + 1
                    )
            self._status.update(
                {
                    "running": False,
                    "finished_at": UTC_CLOCK.now().isoformat(),
                    "current_job_id": None,
                    "current_batch_index": 0,
                }
            )
            return self.get_status()

    async def _prepare_job_tasks(
        self, job: DownloadJob, fetch_result: dict
    ) -> Tuple[List[dict], Dict[str, dict], List[str], List[str], List[int]]:
        """准备任务数据与歌曲详情映射；在此阶段尝试同音质复制优化并过滤出待下载任务。"""

        detailed_tracks = fetch_result.get("tracks", [])  # 歌曲详情列表
        effective_ids = fetch_result.get(
            "effective_ids", []
        )  # 过滤后的有效歌曲 ID（排除作业内已有任务）
        failed_ids = fetch_result.get("failed_ids", [])  # 拉取详情失败的歌曲 ID
        detail_map: Dict[str, dict] = {}  # music_id → 歌曲详情字典
        for track in detailed_tracks:
            music_id = str(track.get("id"))
            if not music_id:
                continue
            detail_map[music_id] = track

        # 构造任务数据（从详细信息映射元数据）
        tasks_data: List[dict] = []  # 待创建的下载任务数据列表
        copied_task_ids: List[int] = []  # 已通过复制优化直接完成的任务 ID 列表
        for music_id in effective_ids:
            detail = detail_map.get(music_id, {})
            title = detail.get("name") or ""
            artists = [a.get("name") for a in detail.get("ar", []) if a.get("name")]
            artist = ", ".join(artists) if artists else ""
            album = (detail.get("al") or {}).get("name") or ""
            data = {
                "music_id": music_id,
                "job_id": job.id,  # 当前作业 ID
                "music_title": title,
                "music_artist": artist,
                "music_album": album,
                "status": "pending",
            }
            copied_id = await self._try_copy_existing(job, data)  # 尝试同音质复制优化
            if copied_id:
                copied_task_ids.append(copied_id)
            else:
                tasks_data.append(data)
        return (
            tasks_data,
            detail_map,
            failed_ids,
            fetch_result.get("skipped_existing_ids", []),
            copied_task_ids,
        )

    async def _handle_batches(
        self,
        job: DownloadJob,
        tasks_data: List[dict],
        detail_map: Dict[str, dict],
        batch_size: int,
    ) -> int:
        """执行批次创建与调度；为每个批次创建任务、写入缓存并等待所有子流程完成。"""
        submitted_ids: List[int] = []  # 已提交任务 ID 列表
        batch_index = 0
        for i in range(0, len(tasks_data), batch_size):
            batch = tasks_data[i : i + batch_size]
            if not batch:
                continue
            batch_index += 1
            self._status["current_batch_index"] = batch_index
            logger.info(
                f"Starting batch {batch_index} for job {job.id} with {len(batch)} tasks"
            )
            created = await self._create_pending_batch(job, batch)  # 创建待下载任务记录

            # 预注入 song_detail 到缓存，避免后续重复请求
            registry = get_task_cache_registry()
            for task in created:
                cache = await registry.get_or_create(task.id, task.music_id)
                cache.song_detail = detail_map.get(task.music_id)

            # 调度下载子流程并等待完成
            await self._dispatch_and_wait_batch(job, created)
            submitted_ids.extend([t.id for t in created])
        return len(submitted_ids)

    async def _create_pending_batch(
        self, job: DownloadJob, batch: List[dict]
    ) -> List[DownloadTask]:
        """批量创建待下载任务并更新作业统计。"""
        created: List[DownloadTask] = []  # 创建后的任务列表
        async with self.uow_factory() as uow:
            created = await self.task_repo.create_batch(uow.session, batch)
            await self.job_repo.update_statistics(
                uow.session, job.id, total_tasks=(job.total_tasks or 0) + len(created)
            )
        return created

    async def _try_copy_existing(self, job: DownloadJob, data: dict) -> int | None:
        """尝试基于同音质来源任务进行文件复制并直接完成当前任务；失败则返回 None。"""
        source_task: DownloadTask | None = None  # 来源任务对象（若存在且音质匹配）
        async with self.uow_factory() as uow:
            source_task = await self.task_repo.find_completed_by_music_and_quality(
                uow.session, data["music_id"], job.target_quality
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
                    target_path.parent.mkdir(
                        parents=True, exist_ok=True
                    )  # 确保目标目录存在
                    shutil.copy2(source_task.file_path, str(target_path))  # 复制文件
                    await self.task_repo.update(
                        uow.session,
                        new_task.id,
                        status="completed",
                        quality=source_task.quality,
                        file_path=str(target_path),
                        file_name=target_path.name,
                        file_format=source_task.file_format,
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
                if isinstance(res, Exception):
                    logger.warning(f"Batch task future {created[idx].id} raised: {res}")

    async def _fetch_playlist_tracks(
        self, job_id: int, playlist_id: str, max_retries: int = 3
    ) -> dict:
        """获取歌单曲目 ID 并批量拉取歌曲详情；包含退避重试与作业内去重。"""
        delay = 1.0  # 初始退避延迟秒数
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
                    "skipped_existing_ids": [],
                }
            except Exception as e:
                logger.warning(
                    f"Fetch playlist detail failed for {playlist_id} (attempt {attempt + 1}): {e}"
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 8.0)

        # 作业内去重：排除已存在任务
        existing_ids: set[str] = set()  # 当前作业已存在任务的 music_id 集合
        async with self.uow_factory() as uow:
            existing_tasks = await self.task_repo.list_by_job(uow.session, job_id)
            for t in existing_tasks:
                if t.music_id:
                    existing_ids.add(str(t.music_id))

        effective_ids = [
            mid for mid in all_ids if mid not in existing_ids
        ]  # 作业内新任务的歌曲 ID
        skipped_existing_ids = [
            mid for mid in all_ids if mid in existing_ids
        ]  # 已存在任务的歌曲 ID
        detailed_tracks: List[dict] = []  # 拉取到的歌曲详情
        failed_ids: List[str] = []  # 拉取失败的歌曲 ID
        chunk_size = 300  # 详情拉取的分块大小；避免接口长度与频率限制
        for i in range(0, len(effective_ids), chunk_size):
            chunk = effective_ids[i : i + chunk_size]
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
            "skipped_existing_ids": skipped_existing_ids,
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
