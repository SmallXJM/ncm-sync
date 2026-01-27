from typing import Optional, Dict, Any
import time
from ncm.client import APIResponse
from ncm.core.logging import get_logger
from ncm.server.decorators import ncm_service
from ncm.core.time import UTC_CLOCK


logger = get_logger(__name__)


class ConfigController:
    def __init__(self):
        from ncm.core.config import get_config_manager
        self._cfgm = get_config_manager()

    def _scrub_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from config dictionary before sending to client."""
        import copy
        safe_data = copy.deepcopy(data)
        
        if "auth" in safe_data:
            auth = safe_data["auth"]
            # Hide secret key
            if "secret_key" in auth:
                del auth["secret_key"]
                
            # Hide passwords
            if "user" in auth:
                del auth["user"]["password"]
                del auth["user"]["password_changed_at"]
        
        return safe_data

    @ncm_service("/ncm/config", ["GET"])
    async def get_config(self, **kwargs) -> APIResponse:
        try:
            cfg = await self._cfgm.load()
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "Config loaded",
                    "data": self._scrub_sensitive_data(cfg.model_dump())
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

    @ncm_service("/ncm/config/refresh_secret_key", ["POST"])
    async def refresh_secret_key(self, **kwargs) -> APIResponse:
        try:
            from ncm.core.config import generate_secret_key
            new_key = generate_secret_key()
            # Update only secret_key
            await self._cfgm.update({"auth": {"secret_key": new_key}})
            return APIResponse(
                status=200,
                body={"code": 200, "message": "Secret key refreshed"}
            )
        except Exception as e:
            logger.exception("Failed to refresh secret key")
            return APIResponse(status=500, body={"code": 500, "message": str(e)})

    @ncm_service("/ncm/config", ["POST"])
    async def update_config(self,
                            download: Optional[dict] = None,
                            subscription: Optional[dict] = None,
                            auth: Optional[dict] = None,
                            **kwargs) -> APIResponse:
        try:
            
            partial = {}

            # Support nested update
            if download is not None:
                partial["download"] = download
            if subscription is not None:
                partial["subscription"] = subscription
            
            if auth is not None:
                # Handle user password preservation logic
                if "user" in auth and isinstance(auth["user"], dict):
                    current_config = await self._cfgm.load()
                    
                    current_user = current_config.auth.user
                    new_user = auth["user"].copy()
                    
                    # 密码为空表示未修改密码
                    if not new_user.get("password"):
                        new_user["password"] = current_user.password
                        # Keep original password_changed_at if not changing password
                        if hasattr(current_user, "password_changed_at"):
                            new_user["password_changed_at"] = current_user.password_changed_at
                    else:
                        new_user["password_changed_at"] = UTC_CLOCK.now().timestamp()
                        

                    auth["user"] = new_user
                    
                if "rotate_secret_key" in auth and auth["rotate_secret_key"]:
                    del auth["rotate_secret_key"]
                    # Rotate secret key
                    from ncm.core.config import generate_secret_key
                    new_key = generate_secret_key()
                    auth["secret_key"] = new_key
                
                if "logout" in auth:
                    if auth["logout"]:
                        # Force logout by updating password_changed_at
                        if "user" in auth and isinstance(auth["user"], dict):
                            auth["user"]["password_changed_at"] = UTC_CLOCK.now().timestamp()
                        else:
                            current_config = await self._cfgm.load()
                            user_data = current_config.auth.user.model_dump()
                            user_data["password_changed_at"] = UTC_CLOCK.now().timestamp()
                            auth["user"] = user_data
                    del auth["logout"]

                partial["auth"] = auth
                logger.info(f"Updating auth with: {auth}")

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
                    "data": self._scrub_sensitive_data(cfg.model_dump())
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
