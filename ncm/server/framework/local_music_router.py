from __future__ import annotations

import hashlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, JSONResponse

from ncm.core.logging import get_logger
from ncm.service.download.service.async_task_service import AsyncTaskService
from ncm.service.music import (
    LocalMusicService,
    LocalMusicNotFoundError,
    LocalMusicNoCoverError,
)

logger = get_logger(__name__)


def register_local_music_routes(app: FastAPI) -> None:
    task_service = AsyncTaskService()
    service = LocalMusicService(task_service)

    @app.get("/local/music/detail/{task_id}", include_in_schema=False)
    async def local_music_detail(task_id: int):
        result = await service.get_detail(task_id)
        return JSONResponse(status_code=result["status"], content=result["body"])

    @app.get("/local/music/cover/{task_id}", include_in_schema=False)
    async def local_music_cover(task_id: int, request: Request):
        task = await task_service.get_task(task_id)
        if not task or not task.file_path:
            raise HTTPException(status_code=404, detail="not found")

        try:
            result = await service.get_cover(task_id)
        except LocalMusicNotFoundError:
            raise HTTPException(status_code=404, detail="not found")
        except LocalMusicNoCoverError:
            raise HTTPException(status_code=404, detail="no cover")

        content = result["content"]
        media_type = result["media_type"]
        last_modified = task.updated_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if task.updated_at else None
        etag = f'"{hashlib.sha1(content).hexdigest()}"'

        if request.headers.get("if-none-match") == etag:
            headers = {
                "Cache-Control": "public, max-age=604800",
                "ETag": etag,
            }
            if last_modified:
                headers["Last-Modified"] = last_modified
            return Response(status_code=304, headers=headers)

        headers = {
            "Cache-Control": "public, max-age=604800",
            "ETag": etag,
            "X-Content-Type-Options": "nosniff",
        }
        if last_modified:
            headers["Last-Modified"] = last_modified

        return Response(content=content, media_type=media_type, headers=headers)

    @app.get("/local/music/stream/{task_id}", include_in_schema=False)
    async def local_music_stream(task_id: int):
        try:
            result = await service.get_stream(task_id)
        except LocalMusicNotFoundError:
            raise HTTPException(status_code=404, detail="not found")

        file_path = result["file_path"]
        media_type = result["media_type"]

        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=media_type,              
            headers={
                "Accept-Ranges": "bytes",        
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.post("/local/music/delete", include_in_schema=False)
    async def local_music_delete(payload: dict):
        result = await service.delete(payload.get("task_id"))
        return JSONResponse(status_code=result["status"], content=result["body"])

    @app.post("/local/music/rename", include_in_schema=False)
    async def local_music_rename(payload: dict):
        result = await service.rename(payload.get("task_id"), payload.get("new_name"))
        return JSONResponse(status_code=result["status"], content=result["body"])


