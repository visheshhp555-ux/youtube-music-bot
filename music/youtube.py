import asyncio
import logging
from typing import Optional

import yt_dlp

logger = logging.getLogger(__name__)


YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "skip_download": True,
    "source_address": "0.0.0.0",
}


def _search_sync(query: str) -> Optional[dict]:
    options = {
        **YDL_BASE_OPTS,
        "default_search": "ytsearch1",
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(query, download=False)

        if not info:
            return None

        entries = info.get("entries")

        if entries:
            entry = next((item for item in entries if item), None)
        else:
            entry = info

        if not entry:
            return None

        return {
            "id": entry.get("id"),
            "title": entry.get("title") or "Unknown Title",
            "channel": (
                entry.get("channel")
                or entry.get("uploader")
                or "Unknown Artist"
            ),
            "duration": entry.get("duration") or 0,
            "url": entry.get("webpage_url"),
            "thumbnail": entry.get("thumbnail"),
        }

    except Exception:
        logger.exception("YouTube search failed")
        return None


def _extract_stream_sync(video_url: str) -> Optional[str]:
    options = {
        **YDL_BASE_OPTS,
        "format": "bestaudio/best",
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            return None

        # Prefer the direct URL supplied by yt-dlp.
        stream_url = info.get("url")

        if stream_url:
            return stream_url

        # Fallback: select an audio format.
        formats = info.get("formats") or []

        audio_formats = [
            fmt
            for fmt in formats
            if fmt.get("url")
            and (
                fmt.get("vcodec") == "none"
                or fmt.get("acodec") not in (None, "none")
            )
        ]

        if not audio_formats:
            return None

        audio_formats.sort(
            key=lambda fmt: (
                fmt.get("abr") or 0,
                fmt.get("asr") or 0,
            ),
            reverse=True,
        )

        return audio_formats[0].get("url")

    except Exception:
        logger.exception("YouTube stream extraction failed")
        return None


async def search_youtube(query: str) -> Optional[dict]:
    """Search YouTube without blocking the bot event loop."""

    query = query.strip()

    if not query:
        return None

    return await asyncio.to_thread(_search_sync, query)


async def get_stream_url(video_url: str) -> Optional[str]:
    """Extract a temporary direct audio stream URL."""

    if not video_url:
        return None

    return await asyncio.to_thread(
        _extract_stream_sync,
        video_url,
    )
