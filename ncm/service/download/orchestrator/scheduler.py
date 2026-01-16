import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone
from ncm.infrastructure.utils.time import TIMEZONE_SYSTEM
from ncm.service.download.orchestrator.process import DownloadProcess

from ncm.core.logging import get_logger

logger = get_logger(__name__)


class ProcessScheduler:
    def __init__(self, process: DownloadProcess):
        self.process = process
        self._scheduler = AsyncIOScheduler(timezone=TIMEZONE_SYSTEM.get())  # 确保使用系统时区
        self._lock = asyncio.Lock()
        self._job = None
        self._cron_expr: Optional[str] = None
        self._batch_size: int = 10

    async def _job_fn(self):
        if self._lock.locked():
            return
        async with self._lock:
            logger.info(f"开始执行下载任务，批次大小: {self._batch_size}")
            await self.process.start(batch_size=self._batch_size)

    def start_scheduler(self):
        if not self._scheduler.running:
            self._scheduler.start()

    def set_cron(self, cron_expr: str):
        self._cron_expr = cron_expr
        self.start_scheduler()
        if self._job:
            try:
                self._scheduler.remove_job(self._job.id)
            except Exception:
                pass
            self._job = None
            # 尝试构造 CronTrigger，确保 APScheduler 能接受
        parts = cron_expr.split()
        try:
            if len(parts) == 5:
                trigger = CronTrigger.from_crontab(
                    cron_expr, timezone=TIMEZONE_SYSTEM.get()
                )  # 五字段标准 crontab
            else:
                # 六字段秒级 cron
                trigger = CronTrigger(
                    second=parts[0],
                    minute=parts[1],
                    hour=parts[2],
                    day=parts[3],
                    month=parts[4],
                    day_of_week=parts[5],
                    timezone=TIMEZONE_SYSTEM.get(),  # 使用系统时区
                )
        except Exception as e:
            raise ValueError(f"cron_expr 无效: {e}")
        self._job = self._scheduler.add_job(
            self._job_fn,
            trigger=trigger,
            id="download_process_cron",
            replace_existing=True,
            max_instances=1,
            coalesce=False,
            misfire_grace_time=30,
        )
        return True

    def enable(self):
        if not self._cron_expr:
            return False
        if not self._scheduler.running:
            self._scheduler.start()
        if not self._job:
            return self.set_cron(self._cron_expr, self._batch_size)
        return True

    def disable(self):
        if self._job:
            try:
                self._scheduler.remove_job(self._job.id)
            except Exception:
                pass
            self._job = None
        return True

    def next_run_time(self) -> Optional[str]:
        if self._job and self._job.next_run_time:
            return self._job.next_run_time.isoformat()
        return None

    def get_stats(self) -> dict:
        return {
            "is_running": self._scheduler.running,
            "next_run_time": self.next_run_time(),
        }

    def set_batch_size(self, batch_size: int):
        self._batch_size = int(batch_size)
        return True

    def get_config(self) -> dict:
        return {
            "cron_expr": self._cron_expr,
            "batch_size": self._batch_size,
            "next_run_time": self.next_run_time(),
        }

    async def cleanup(self):
        try:
            if self._job:
                try:
                    self._scheduler.remove_job(self._job.id)
                except Exception:
                    pass
            if self._scheduler.running:
                self._scheduler.shutdown(wait=False)
        except Exception:
            pass
