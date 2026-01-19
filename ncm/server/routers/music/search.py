"""Search HTTP controller for music search functionality."""

import logging
from typing import Dict, Any
from ncm.client import APIResponse
from ncm.server.decorators import ncm_service
from ncm.service.cookie.decorators import with_cookie

logger = logging.getLogger(__name__)


class SearchController:
    """HTTP controller for music search functionality."""
    
    def __init__(self):
        """Initialize search controller."""
        pass
    
    @ncm_service("/ncm/music/search", ["POST"])
    @with_cookie(max_retries=2)
    async def enhanced_search(self, keywords: str, search_type: str = "song", 
                            limit: int = 30, offset: int = 0, 
                            include_details: bool = False, **kwargs) -> APIResponse:
        """
        Enhanced search with optional detail fetching.
        
        Args:
            keywords: Search keywords
            search_type: Type of search (song, album, artist, playlist)
            limit: Number of results
            offset: Offset for pagination
            include_details: Whether to fetch detailed info for each result
        """
        try:
            # Import modules here to avoid circular imports
            from ncm.client.apis import search

            # Perform basic search
            search_response = await search.get(
                keywords=keywords,
                type=search_type,
                limit=limit,
                offset=offset,
                **kwargs
            )
            
            if not search_response.success:
                return APIResponse(
                    status=search_response.status,
                    body={
                        "code": search_response.code,
                        "message": f"搜索失败: {search_response.message}",
                        "error": search_response.body
                    }
                )
            
            results = search_response.body
            
            # If details requested, fetch additional info
            if include_details and search_type == "song":
                results = await self._enhance_song_results(results, **kwargs)
            elif include_details and search_type == "album":
                results = await self._enhance_album_results(results, **kwargs)
            elif include_details and search_type == "playlist":
                results = await self._enhance_playlist_results(results, **kwargs)
            
            return APIResponse(
                status=200,
                body={
                    "code": 200,
                    "message": "增强搜索成功",
                    "data": {
                        "search_type": search_type,
                        "keywords": keywords,
                        "results": results,
                        "enhanced": include_details
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"增强搜索失败: {str(e)}")
            return APIResponse(
                status=500,
                body={
                    "code": 500,
                    "message": f"增强搜索失败: {str(e)}"
                }
            )
    
    async def _enhance_song_results(self, search_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Enhance song search results with additional details."""
        try:
            songs = search_results.get("result", {}).get("songs", [])
            if not songs:
                return search_results
            
            # Get detailed info for top results (limit to avoid API overload)
            song_ids = [str(song["id"]) for song in songs[:20]]

            from ncm.client.apis import song
            detail_response = await song.detail(ids=",".join(song_ids), **kwargs)
            
            if detail_response.success:
                detailed_songs = detail_response.body.get("songs", [])
                detail_map = {str(s["id"]): s for s in detailed_songs}
                
                # Merge detailed info
                for song_item in songs:
                    song_id = str(song_item["id"])
                    if song_id in detail_map:
                        song_item["detailed_info"] = detail_map[song_id]
            
            return search_results
            
        except Exception as e:
            logger.error(f"增强歌曲搜索结果失败: {str(e)}")
            return search_results
    
    async def _enhance_album_results(self, search_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Enhance album search results with additional details."""
        # Implementation for album enhancement
        return search_results
    
    async def _enhance_playlist_results(self, search_results: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Enhance playlist search results with additional details."""
        # Implementation for playlist enhancement
        return search_results