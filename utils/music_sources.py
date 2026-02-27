"""
Music source utilities for MusikBOT.
Handles YouTube search/extraction and query routing.
"""

import re
import logging
from typing import Optional

import yt_dlp

logger = logging.getLogger("musikbot.sources")

# yt-dlp options for audio extraction
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extract_flat": False,
}

# FFmpeg options for discord.py voice
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# URL patterns
YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
)


class TrackInfo:
    """Represents a resolved track ready for playback."""

    def __init__(
        self,
        title: str,
        url: str,
        stream_url: str,
        duration: int = 0,
        thumbnail: Optional[str] = None,
        requester: Optional[str] = None,
    ):
        self.title = title
        self.url = url
        self.stream_url = stream_url
        self.duration = duration
        self.thumbnail = thumbnail
        self.requester = requester

    @property
    def duration_str(self) -> str:
        """Format duration as MM:SS."""
        if not self.duration:
            return "Live"
        minutes, seconds = divmod(self.duration, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def __str__(self) -> str:
        return f"{self.title} [{self.duration_str}]"


class MusicSourceError(Exception):
    """Raised when a music source lookup fails."""
    pass


async def search_youtube(query: str) -> Optional[TrackInfo]:
    """
    Search YouTube for a query string and return the best match.
    """
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if not info or "entries" not in info or not info["entries"]:
                return None

            entry = info["entries"][0]
            return TrackInfo(
                title=entry.get("title", "Unknown"),
                url=entry.get("webpage_url", ""),
                stream_url=entry.get("url", ""),
                duration=entry.get("duration", 0),
                thumbnail=entry.get("thumbnail"),
            )
    except Exception as e:
        logger.error(f"YouTube search failed for '{query}': {e}")
        raise MusicSourceError(f"Could not find anything for: {query}") from e


async def get_youtube_audio(url: str) -> Optional[TrackInfo]:
    """Extract audio stream from a direct YouTube URL."""
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None

            return TrackInfo(
                title=info.get("title", "Unknown"),
                url=info.get("webpage_url", url),
                stream_url=info.get("url", ""),
                duration=info.get("duration", 0),
                thumbnail=info.get("thumbnail"),
            )
    except Exception as e:
        logger.error(f"YouTube extraction failed for '{url}': {e}")
        raise MusicSourceError(f"Could not extract audio from: {url}") from e


async def resolve_query(query: str) -> Optional[TrackInfo]:
    """
    Smart query router:
    - YouTube URL → direct extraction
    - Plain text → YouTube search
    """
    query = query.strip()

    # YouTube URL
    if YOUTUBE_REGEX.match(query):
        logger.info(f"Detected YouTube URL: {query}")
        return await get_youtube_audio(query)

    # Plain text search → YouTube
    logger.info(f"Searching YouTube for: {query}")
    return await search_youtube(query)
