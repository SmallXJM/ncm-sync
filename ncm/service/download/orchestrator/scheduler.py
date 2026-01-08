import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class ProcessScheduler:
    def __init__(self, process):
        self.process = process
        self._scheduler = AsyncIOScheduler()
        self._lock = asyncio.Lock()
        self._job = None
        self._cron_expr: Optional[str] = None
        self._batch_size: int = 10

    async def _job_fn(self):
        if self._lock.locked():
            return
        async with self._lock:
            await self.process.start(batch_size=self._batch_size)

    def start_scheduler(self):
        if not self._scheduler.running:
            self._scheduler.start()

    def set_cron(self, cron_expr: str, batch_size: int = 10):
        self._cron_expr = cron_expr
        self._batch_size = batch_size
        self.start_scheduler()
        if self._job:
            try:
                self._scheduler.remove_job(self._job.id)
            except Exception:
                pass
            self._job = None
        trigger = CronTrigger.from_crontab(cron_expr)
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
