from typing import Optional
from ncm.client import APIResponse
from ncm.core.logging import get_logger
from ncm.api import ncm_service

logger = get_logger(__name__)


class ConfigController:
    def __init__(self):
        from ncm.core.config import get_config_manager
        self._cfgm = get_config_manager()

    @ncm_service("/ncm/config", ["GET"])
    async def get_config(self, **kwargs) -> APIResponse:
        try:
            cfg = await self._cfgm.load()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Config loaded",
                    "data": cfg.dict()
                }
            )
        except Exception as e:
            logger.exception("Failed to load config")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to load config: {str(e)}"
                }
            )

    @ncm_service("/ncm/config", ["POST"])
    async def update_config(self,
                            download: Optional[dict] = None,
                            subscription: Optional[dict] = None,
                            **kwargs) -> APIResponse:
        try:
            
            partial = {}

            # Support nested update
            if download is not None:
                partial["download"] = download
            if subscription is not None:
                partial["subscription"] = subscription
            
            # Support flat update (backward compatibility)
            # Map flat keys to nested structure
            flat_download = {}
            flat_subscription = {}
            
            # Download settings
            if "cron_expr" in kwargs:
                flat_download["cron_expr"] = kwargs["cron_expr"]
            if "max_concurrent_downloads" in kwargs:
                flat_download["max_concurrent_downloads"] = int(kwargs["max_concurrent_downloads"])
            if "max_threads_per_download" in kwargs:
                flat_download["max_threads_per_download"] = int(kwargs["max_threads_per_download"])
            if "temp_downloads_dir" in kwargs:
                flat_download["temp_downloads_dir"] = kwargs["temp_downloads_dir"]
            
            # Subscription settings
            if "default_filename_template" in kwargs:
                flat_subscription["filename"] = kwargs["default_filename_template"]
                
            # Merge flat settings if they exist and weren't provided in nested dicts
            if flat_download:
                if "download" not in partial:
                    partial["download"] = {}
                partial["download"].update(flat_download)
                
            if flat_subscription:
                if "subscription" not in partial:
                    partial["subscription"] = {}
                partial["subscription"].update(flat_subscription)

            if not partial:
                return APIResponse(
                    status=400,
                    body={
                        "code": 400,
                        "message": "No valid config parameters provided. Please check your request body and Content-Type."
                    }
                )

            logger.info(f"Updating config with: {partial}")
            cfg = await self._cfgm.update(partial)

            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Config updated",
                    "data": cfg.dict()
                }
            )
        except Exception as e:
            logger.exception("Failed to update config")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"Failed to update config: {str(e)}"
                }
            )
