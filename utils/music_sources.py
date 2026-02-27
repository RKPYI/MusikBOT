"""
Music source utilities for MusikBOT.
Handles YouTube search/extraction and query routing.
"""

import asyncio
import os
import re
import logging
from pathlib import Path
from typing import Optional

import yt_dlp

logger = logging.getLogger("musikbot.sources")

# ─── YouTube Authentication ───────────────────────────────────────────────────
# Cloud/VPS IPs are flagged by YouTube and REQUIRE cookies to work.
# Place a cookies.txt (Netscape format) in the project root.
#
# Export steps (one-time, lasts weeks/months):
#   1. Open an incognito window → log into YouTube
#   2. Navigate to https://www.youtube.com/robots.txt
#   3. Use "Get cookies.txt LOCALLY" extension to export cookies.txt
#   4. Close the incognito window (don't reuse that session in the browser)
#   5. Copy cookies.txt to the project root next to bot.py
#
# The PO Token plugin (bgutil-ytdlp-pot-provider) + Node.js runtime
# handle token generation automatically once cookies authenticate you.
_COOKIES_FILE = Path(__file__).resolve().parent.parent / "cookies.txt"
_COOKIES_FROM_BROWSER = os.getenv("COOKIES_FROM_BROWSER")

# yt-dlp options for audio extraction
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extract_flat": False,
    # Node.js runtime for JS challenges & PO Token generation
    "js_runtimes": {"node": {}},
}

# Apply cookie settings — required on cloud/VPS servers
if _COOKIES_FILE.is_file():
    YDL_OPTIONS["cookiefile"] = str(_COOKIES_FILE)
    logger.info("Using cookies from %s", _COOKIES_FILE)
elif _COOKIES_FROM_BROWSER:
    YDL_OPTIONS["cookiesfrombrowser"] = (_COOKIES_FROM_BROWSER,)
    logger.info("Using cookies from browser: %s", _COOKIES_FROM_BROWSER)
else:
    logger.warning(
        "No cookies.txt found! YouTube will likely block requests from this server. "
        "See utils/music_sources.py for export instructions."
    )

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
    Runs yt-dlp in a thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    try:
        def _extract():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                return ydl.extract_info(f"ytsearch:{query}", download=False)

        info = await loop.run_in_executor(None, _extract)
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
    """Extract audio stream from a direct YouTube URL.
    Runs yt-dlp in a thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    try:
        def _extract():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, _extract)
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
