"""Music download controller with new task-driven architecture."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from ncm.client import APIResponse
from ncm.server.routers.download import DownloadContext
from ncm.core.logging import get_logger

logger = get_logger(__name__)


class DownloadControllerDashboard:
    def __init__(self, context: DownloadContext):
        # self.ctx = context
        self.orchestrator = context.orchestrator
        self._scheduler = context.scheduler
        self.process = context.process

    async def aggregate(self, **kwargs) -> APIResponse:
        try:
            days = await self._get_recent_added_music_days()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Dashboard aggregate retrieved successfully",
                    "data": {
                        "recent_added_music": {
                            "days": days,
                        },
                    },
                },
            )
        except Exception as e:
            logger.exception("Failed to get dashboard aggregate")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to get dashboard aggregate: {str(e)}",
                },
            )

    async def _get_recent_added_music_days(self) -> list[dict[str, int | str]]:
        timezone_info = self._get_dashboard_timezone()
        today = datetime.now(timezone_info).date()
        start_day = today - timedelta(days=6)
        end_day = today + timedelta(days=1)

        start_local = datetime.combine(start_day, time.min, tzinfo=timezone_info)
        end_local = datetime.combine(end_day, time.min, tzinfo=timezone_info)
        # SQLite stores naive datetimes in this project, with UTC implied.
        start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)

        async with self.orchestrator.uow_factory() as uow:
            counts = await self.orchestrator.task_repo.count_completed_by_day(
                uow.session,
                start_utc,
                end_utc,
                timezone_info,
            )

        return [
            {
                "date": (start_day + timedelta(days=offset)).isoformat(),
                "count": counts.get((start_day + timedelta(days=offset)).isoformat(), 0),
            }
            for offset in range(7)
        ]

    def _get_dashboard_timezone(self) -> ZoneInfo:
        return ZoneInfo("Asia/Shanghai")
