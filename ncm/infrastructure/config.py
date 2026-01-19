from __future__ import annotations
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DownloadSettings(BaseModel):
    # 默认值：凌晨两点执行一次
    cron_expr: Optional[str] = Field(default="0 2 * * *")
    # 最大并发量
    max_concurrent_downloads: int = Field(default=3, ge=1, le=100)
    # 单个下载最大线程数
    max_threads_per_download: int = Field(default=4, ge=1, le=64)
    temp_downloads_dir: str = Field(default="downloads")

    @field_validator("cron_expr")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("cron_expr 不能为空字符串")

        parts = v.split()
        if len(parts) not in (5, 6):
            raise ValueError(f"cron_expr 字段数错误: got {len(parts)}, expected 5 or 6")
        return v



class SubscriptionSettings(BaseModel):
    target_quality: str = Field(default=r"hires")
    embed_metadata: bool = Field(default=True)
    embed_cover: bool = Field(default=True)
    embed_lyrics: bool = Field(default=True)
    filename: str = Field(default=r"{artist} - {title}")
    filename: str = Field(default=r"{artist} - {title}")
    # 歌单下载目录
    music_dir_playlist: str = Field(default=r"歌单/{user_name}/{playlist_name}")


class NcmConfig(BaseModel):
    download: DownloadSettings = Field(default_factory=DownloadSettings)
    subscription: SubscriptionSettings = Field(default_factory=SubscriptionSettings)


from ncm.infrastructure.utils.path import get_data_path, normalize_path

class ConfigManager:
    def __init__(self, path: Optional[str] = None):
        if path:
            self._path = path
        else:
            self._path = str(get_data_path("config.json"))
        self._lock = asyncio.Lock()
        self._config = NcmConfig()
        self._loaded = False
        self._observers = []

    def add_observer(self, callback):
        """Add a callback to be notified when config is updated.
        Callback receives the new NcmConfig object.
        """
        self._observers.append(callback)

    def remove_observer(self, callback):
        """Remove a callback from observers."""
        if callback in self._observers:
            self._observers.remove(callback)

    def path(self) -> str:
        return normalize_path(self._path)

    def get(self) -> Dict[str, Any]:
        return self._config.dict()

    def model(self) -> NcmConfig:
        return self._config

    async def load(self) -> NcmConfig:
        if self._loaded:
            return self._config
        async with self._lock:
            try:
                config_path = Path(self.path())
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._config = NcmConfig(**(data or {}))
                self._loaded = True
            except Exception:
                self._config = NcmConfig()
                self._loaded = True
        return self._config

    def load_sync(self) -> NcmConfig:
        if self._loaded:
            return self._config
        try:
            config_path = Path(self.path())
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._config = NcmConfig(**(data or {}))
            self._loaded = True
        except Exception:
            self._config = NcmConfig()
            self._loaded = True
        return self._config

    def ensure_loaded_sync(self) -> NcmConfig:
        return self.load_sync()

    async def save(self) -> bool:
        async with self._lock:
            try:
                with open(self.path(), "w", encoding="utf-8") as f:
                    json.dump(self._config.dict(), f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    def save_sync(self) -> bool:
        try:
            with open(self.path(), "w", encoding="utf-8") as f:
                json.dump(self._config.dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    async def update(self, partial: Dict[str, Any]) -> NcmConfig:
        async with self._lock:
            current_dict = self._config.dict()
            self._deep_update(current_dict, partial or {})
            self._config = NcmConfig(**current_dict)
        await self.save()

        for callback in self._observers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._config)
                else:
                    callback(self._config)
            except Exception:
                pass

        return self._config

    def _deep_update(self, target: Dict, source: Dict):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value


_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
