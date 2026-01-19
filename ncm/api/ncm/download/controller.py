"""Music download controller with new task-driven architecture."""

from fastapi import WebSocket

from ncm.api.ncm.download import DownloadContext
from ncm.api.ncm.ws import DownloadWsContext, WsRouter
from ncm.api.ncm.download.daemon import DownloadControllerDaemon
from ncm.api.ncm.download.dashboard import DownloadControllerDashboard
from ncm.api.ncm.download.job import DownloadControllerJob
from ncm.api.ncm.download.system import DownloadControllerSystem
from ncm.api.ncm.download.task import DownloadControllerTask
from ncm.service.download.orchestrator import DownloadOrchestrator, DownloadProcess
from ncm.client import APIResponse
from ncm.core.logging import get_logger
from ncm.infrastructure.http import ncm_service, ncm_ws_service
from ncm.infrastructure.config import get_config_manager

logger = get_logger(__name__)


class DownloadController:
    """主控制器：负责资源生命周期管理和路由转发"""

    def __init__(self):
        """Initialize download controller."""

        # 1. 获取配置
        cfgm = get_config_manager()
        cfg = cfgm.ensure_loaded_sync()  # 注意：构造函数中阻塞可能影响启动速度，但在单例/初始化阶段通常可接受

        # 2. 提取配置 (保存当前状态以便做 Diff)
        self._current_cron = cfg.download.cron_expr
        # 显式分离 batch_size 逻辑，增加可读性
        self._current_batch_size = cfg.download.max_concurrent_downloads

        # 3. 初始化核心组件
        self.orchestrator = DownloadOrchestrator(
            downloads_dir=cfg.download.temp_downloads_dir,
            max_concurrent_downloads=cfg.download.max_concurrent_downloads,
            max_threads_per_download=cfg.download.max_threads_per_download
        )
        self.process = DownloadProcess(self.orchestrator)

        # 4. 初始化调度器 (局部引用如果是为了避坑循环依赖)
        from ncm.service.download.orchestrator.scheduler import ProcessScheduler
        self._scheduler = ProcessScheduler(self.process)
        
        # 5. 初始设置 Cron
        self._scheduler.set_batch_size(self._current_batch_size)
        if self._current_cron:
            self._scheduler.set_cron(self._current_cron)

        # 6. 创建上下文对象
        context = DownloadContext(self.orchestrator, self.process, self._scheduler)

        # 7. 实例化子控制器 (组合模式)
        self.jobs = DownloadControllerJob(context)
        self.tasks = DownloadControllerTask(context)
        self.daemon = DownloadControllerDaemon(context)
        self.system = DownloadControllerSystem(context)
        self.dashboard = DownloadControllerDashboard(context)

        # 8. 监听配置变更
        cfgm.add_observer(self._on_config_update)

    # --- 统一的生命周期管理 ---
    async def cleanup(self):
        """统一销毁资源，确保所有组件被正确清理"""
        logger.info("Starting DownloadController cleanup...")
        
        # 1. 移除配置监听
        try:
            cfgm = get_config_manager()
            if hasattr(cfgm, "remove_observer"):
                cfgm.remove_observer(self._on_config_update)
        except Exception as e:
            logger.warning(f"Failed to remove config observer: {e}")

        # 2. 清理调度器
        try:
            if hasattr(self, "_scheduler") and self._scheduler:
                await self._scheduler.cleanup()
                logger.info("Scheduler cleaned up")
        except Exception as e:
            logger.error(f"Scheduler cleanup failed: {e}")

        # 3. 清理下载流程 (停止运行中的任务)
        try:
            if hasattr(self, "process") and self.process:
                if hasattr(self.process, "cleanup"):
                    await self.process.cleanup()
                    logger.info("DownloadProcess cleaned up")
        except Exception as e:
            logger.error(f"DownloadProcess cleanup failed: {e}")

        # 4. 清理编排器 (关闭下载器、连接池等)
        try:
            if hasattr(self, "orchestrator") and self.orchestrator:
                await self.orchestrator.close()
                logger.info("DownloadOrchestrator closed")
        except Exception as e:
            logger.error(f"DownloadOrchestrator cleanup failed: {e}")
            
        logger.info("DownloadController cleanup completed")

    async def _on_config_update(self, config):
        """Handle dynamic config updates safely and efficiently."""
        try:
            dl_cfg = config.download

            self.orchestrator.update_concurrency_settings(
                max_concurrent=dl_cfg.max_concurrent_downloads,
                max_threads=dl_cfg.max_threads_per_download
            )

            # 只有当 cron 表达式或 batch_size 真的改变时才重置调度器
            new_cron = dl_cfg.cron_expr
            new_batch_size = dl_cfg.max_concurrent_downloads

            should_update_scheduler = (
                    new_cron != self._current_cron or
                    new_batch_size != self._current_batch_size
            )

            if should_update_scheduler:
                logger.info(
                    f"Config change detected: Cron '{self._current_cron}'->'{new_cron}', Batch {self._current_batch_size}->{new_batch_size}")

                if new_cron:
                    # 更新状态
                    self._current_cron = new_cron
                    self._current_batch_size = new_batch_size
                    # 应用新配置
                    self._scheduler.set_cron(new_cron)
                    # 如果之前调度器是开启的，可能需要逻辑判断是否要重启/刷新
                else:
                    # 如果新配置把 cron 删了，可能需要停止调度
                    logger.warning("Cron expression removed in config, disabling scheduler task.")
                    self._scheduler.disable()  # 假设有 disable 方法
                    self._current_cron = None

        except AttributeError as e:
            logger.error(f"Config structure mismatch: {e}")
        except Exception:
            logger.exception("Failed to apply download controller config update")

    # --- 路由转发：将请求委托给子控制器 ---
    @ncm_service("/ncm/download/stats", ["GET"])
    async def get_stats(self, **kwargs) -> APIResponse:
        return await self.system.get_stats(**kwargs)

    @ncm_service("/ncm/download/job/create", ["POST"])
    async def create_job(self, **kwargs) -> APIResponse:
        return await self.jobs.create_job(**kwargs)

    @ncm_service("/ncm/download/job", ["GET"])
    async def list_jobs(self, **kwargs) -> APIResponse:
        return await self.jobs.list_jobs(**kwargs)

    @ncm_service("/ncm/download/job/retry", ["POST"])
    async def retry_job_tasks(self, **kwargs) -> APIResponse:
        return await self.jobs.retry_job_tasks(**kwargs)

    @ncm_service("/ncm/download/job/update", ["POST"])
    async def update_job(self, **kwargs) -> APIResponse:
        return await self.jobs.update_job(**kwargs)

    @ncm_service("/ncm/download/job/delete", ["POST"])
    async def delete_job(self, **kwargs) -> APIResponse:
        return await self.jobs.delete_job(**kwargs)

    # ===== TASK MANAGEMENT =====
    @ncm_service("/ncm/download/task/submit", ["POST"])
    async def submit_task(self, **kwargs) -> APIResponse:
        return await self.tasks.submit_task(**kwargs)

    @ncm_service("/ncm/download/task/status", ["GET"])
    async def get_task_status(self, **kwargs) -> APIResponse:
        return await self.tasks.get_task_status(**kwargs)

    @ncm_service("/ncm/download/task/list", ["GET","POST"])
    async def list_tasks(self, **kwargs) -> APIResponse:
        return await self.tasks.list_tasks(**kwargs)

    @ncm_service("/ncm/download/task/cancel", ["POST"])
    async def cancel_task(self, **kwargs) -> APIResponse:
        return await self.tasks.cancel_task(**kwargs)

    @ncm_service("/ncm/download/task/reset", ["POST"])
    async def reset_task(self, **kwargs) -> APIResponse:
        return await self.tasks.reset_task(**kwargs)

    @ncm_service("/ncm/download/task/upgrade_quality", ["GET", "POST"])
    async def upgrade_task_quality(self, **kwargs) -> APIResponse:
        return await self.tasks.submit_task(**kwargs)

    @ncm_service("/ncm/download/daemon/control", ["POST"])
    async def daemon_control(self, **kwargs) -> APIResponse:
        return await self.daemon.daemon_control(**kwargs)

    @ncm_service("/ncm/dashboard/aggregate", ["GET", "POST"])
    async def dashboard_aggregate(self, **kwargs) -> APIResponse:
        return await self.dashboard.aggregate(**kwargs)

    @ncm_ws_service("/ws/ncm")
    async def download_ws(self, websocket: WebSocket):
        context = DownloadWsContext(
            orchestrator=self.orchestrator,
            process=self.process,
            scheduler=self._scheduler,
        )
        router = WsRouter(context)
        await router.handle(websocket)
