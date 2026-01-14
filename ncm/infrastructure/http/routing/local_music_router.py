from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, JSONResponse

from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService

logger = get_logger(__name__)


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child_resolved = child.resolve()
        parent_resolved = parent.resolve()
        return child_resolved == parent_resolved or parent_resolved in child_resolved.parents
    except Exception:
        return False


def _guess_image_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "application/octet-stream"


def _extract_cover_bytes(file_path: Path) -> Optional[bytes]:
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
    except Exception:
        return None

    suffix = file_path.suffix.lower().lstrip(".")
    try:
        if suffix == "mp3":
            audio = MP3(str(file_path))
            if not audio.tags:
                return None
            id3 = ID3(str(file_path))
            for tag in id3.values():
                if tag.FrameID == "APIC":
                    return bytes(tag.data)
            return None

        if suffix in {"m4a", "mp4", "aac"}:
            audio = MP4(str(file_path))
            covr = audio.tags.get("covr") if audio.tags else None
            if not covr:
                return None
            first = covr[0]
            return bytes(first)

        if suffix == "flac":
            audio = FLAC(str(file_path))
            if not audio.pictures:
                return None
            return bytes(audio.pictures[0].data)

        return None
    except Exception:
        return None


def _extract_lyrics(file_path: Path) -> Optional[str]:
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
    except Exception:
        return None

    suffix = file_path.suffix.lower().lstrip(".")
    try:
        if suffix == "mp3":
            audio = MP3(str(file_path))
            if not audio.tags:
                return None
            id3 = ID3(str(file_path))
            uslt = id3.getall("USLT")
            if uslt:
                return str(uslt[0].text)
            sylt = id3.getall("SYLT")
            if sylt:
                pieces = [p[0] for p in sylt[0].text if p and isinstance(p[0], str)]
                return "\n".join(pieces) if pieces else None
            return None

        if suffix in {"m4a", "mp4", "aac"}:
            audio = MP4(str(file_path))
            lyr = audio.tags.get("\xa9lyr") if audio.tags else None
            if lyr:
                return str(lyr[0])
            return None

        if suffix == "flac":
            audio = FLAC(str(file_path))
            lyr = audio.get("LYRICS")
            if lyr:
                return str(lyr[0])
            return None

        return None
    except Exception:
        return None


def register_local_music_routes(app: FastAPI) -> None:
    """
    本地音乐文件接口（仅本地文件操作，不涉及 NCM 外部网络请求）。

    说明：
    - 这些接口用于前端音乐详情页展示与文件管理（播放/封面/重命名/删除）。
    - 为安全起见，所有文件操作都会限制在任务所属 Job 的 storage_path 目录下。
    """

    task_service = AsyncTaskService()

    @app.get("/local/music/detail/{task_id}", include_in_schema=False)
    async def local_music_detail(task_id: int):
        task = await task_service.get_task(int(task_id))
        if not task:
            return JSONResponse(status_code=404, content={"code": 404, "message": "Task not found"})

        file_path = Path(task.file_path) if task.file_path else None
        file_exists = bool(file_path and file_path.exists())

        lyrics = None
        if file_exists and file_path:
            lyrics = _extract_lyrics(file_path)

        return {
            "code": 200,
            "message": "OK",
            "data": {
                "id": task.id,
                "music_id": task.music_id,
                "music_title": task.music_title,
                "music_artist": task.music_artist,
                "music_album": task.music_album,
                "quality": task.quality,
                "file_path": task.file_path,
                "file_name": task.file_name,
                "file_format": task.file_format,
                "file_size": task.file_size,
                "status": task.status,
                "error_message": task.error_message,
                "lyrics": lyrics,
                "file_exists": file_exists,
            },
        }

    @app.get("/local/music/cover/{task_id}", include_in_schema=False)
    async def local_music_cover(task_id: int):
        task = await task_service.get_task(int(task_id))
        if not task or not task.file_path:
            raise HTTPException(status_code=404, detail="not found")

        file_path = Path(task.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="not found")

        cover = _extract_cover_bytes(file_path)
        if not cover:
            raise HTTPException(status_code=404, detail="no cover")

        return Response(content=cover, media_type=_guess_image_mime(cover))

    @app.get("/local/music/stream/{task_id}", include_in_schema=False)
    async def local_music_stream(task_id: int):
        task = await task_service.get_task(int(task_id))
        if not task or not task.file_path:
            raise HTTPException(status_code=404, detail="not found")

        file_path = Path(task.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="not found")

        return FileResponse(path=str(file_path), filename=file_path.name)

    @app.post("/local/music/delete", include_in_schema=False)
    async def local_music_delete(payload: dict):
        task_id = payload.get("task_id")
        if not task_id:
            return JSONResponse(status_code=400, content={"code": 400, "message": "task_id required"})

        task = await task_service.get_task(int(task_id))
        if not task or not task.file_path:
            return JSONResponse(status_code=404, content={"code": 404, "message": "Task/file not found"})

        job = await task_service.get_job_for_task(int(task_id))
        if not job:
            return JSONResponse(status_code=404, content={"code": 404, "message": "Job not found"})

        file_path = Path(task.file_path)
        base = Path(job.storage_path)
        if not _is_within(file_path, base):
            return JSONResponse(status_code=403, content={"code": 403, "message": "Forbidden"})

        try:
            if file_path.exists():
                file_path.unlink()
            await task_service.update_fields(int(task_id), file_path=None, file_name=None, file_size=None)
            return {"code": 200, "message": "OK"}
        except Exception as e:
            logger.exception("Failed to delete local music file")
            return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

    @app.post("/local/music/rename", include_in_schema=False)
    async def local_music_rename(payload: dict):
        task_id = payload.get("task_id")
        new_name = payload.get("new_name")
        if not task_id or not new_name:
            return JSONResponse(status_code=400, content={"code": 400, "message": "task_id and new_name required"})

        task = await task_service.get_task(int(task_id))
        if not task or not task.file_path:
            return JSONResponse(status_code=404, content={"code": 404, "message": "Task/file not found"})

        job = await task_service.get_job_for_task(int(task_id))
        if not job:
            return JSONResponse(status_code=404, content={"code": 404, "message": "Job not found"})

        file_path = Path(task.file_path)
        base = Path(job.storage_path)
        if not _is_within(file_path, base):
            return JSONResponse(status_code=403, content={"code": 403, "message": "Forbidden"})

        if not file_path.exists():
            return JSONResponse(status_code=404, content={"code": 404, "message": "File not found"})

        target_path = file_path.with_name(str(new_name))
        if not _is_within(target_path, base):
            return JSONResponse(status_code=403, content={"code": 403, "message": "Forbidden"})

        try:
            file_path.rename(target_path)
            await task_service.update_fields(int(task_id), file_path=str(target_path), file_name=target_path.name)
            updated = await task_service.get_task(int(task_id))
            return {
                "code": 200,
                "message": "OK",
                "data": updated.to_dict() if updated else None,
            }
        except Exception as e:
            logger.exception("Failed to rename local music file")
            return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

