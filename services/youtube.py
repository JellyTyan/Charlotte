import asyncio
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yt_dlp
from aiofiles import os as aios
from yt_dlp.utils import sanitize_filename

from utils import random_cookie_file, update_metadata

from .base_service import BaseService


class YouTubeService(BaseService):
    name = "Youtube"
    _download_executor = ThreadPoolExecutor(max_workers=10)

    def __init__(self, output_path: str = "other/downloadsTemp") -> None:
        super().__init__()
        self.output_path = output_path

    def _get_video_options(self):
        return {
            "format": "bv*[filesize < 50M][ext=mp4][vcodec^=avc1] + ba[ext=m4a]",
            "outtmpl": f"{self.output_path}/%(id)s_{sanitize_filename('%(title)s')}.%(ext)s",
            "noplaylist": True,
            "cookiefile": random_cookie_file(),
        }

    def _get_audio_options(self):
        return {
            "format": "m4a/bestaudio/best",
            "writethumbnail": True,
            "outtmpl": f"{self.output_path}/%(id)s_{sanitize_filename('%(title)s')}",
            "cookiefile": random_cookie_file(),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }
            ],
        }

    def is_supported(self, url: str) -> bool:
        return bool(
            re.match(
                r"https?://(?:www\.)?(?:m\.)?(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=))([\w-]+)",
                url,
            )
        )

    def is_playlist(self, url: str) -> bool:
        return False

    def supports_format_choice(self) -> bool:
        return True

    async def download(self, url: str, format_choice: Optional[str] = None) -> list:
        if format_choice == "audio":
            return await self.download_audio(url)
        return await self.download_video(url)

    async def download_video(self, url: str) -> list:
        try:
            is_valid, best_format = check_video_size(url)

            if is_valid is False and best_format is None:
                raise ValueError("Youtube Video size is too large")

            options = self._get_video_options()
            options["format"] = f"{best_format['format_id']}+bestaudio[ext=m4a]/best[ext=mp4]/best"
            with yt_dlp.YoutubeDL(options) as ydl:
                loop = asyncio.get_event_loop()

                info_dict = await loop.run_in_executor(
                    self._download_executor,
                    lambda: ydl.extract_info(url, download=False)
                )

                if not info_dict:
                    raise ValueError("Failed to get video info")

                await loop.run_in_executor(
                    self._download_executor,
                    lambda: ydl.download([url])
                )

                return [{
                    "type": "video",
                    "path": ydl.prepare_filename(info_dict),
                    "title": info_dict.get("title", "video"),
                    "width": info_dict.get("width", 0),
                    "height": info_dict.get("height", 0),
                    "duration": info_dict.get("duration", 0),
                }]

        except Exception as e:
            logging.error(f"YouTube video error: {str(e)}", exc_info=True)
            raise

    async def download_audio(self, url: str) -> list:
        try:
            options = self._get_audio_options()
            with yt_dlp.YoutubeDL(options) as ydl:
                loop = asyncio.get_event_loop()

                info_dict = await loop.run_in_executor(
                    self._download_executor,
                    lambda: ydl.extract_info(url, download=False)
                )
                if not info_dict:
                    raise ValueError("Failed to get audio info")

                await loop.run_in_executor(
                    self._download_executor,
                    lambda: ydl.download([url])
                )

                base_path = os.path.join(
                    self.output_path,
                    f"{info_dict['id']}_{sanitize_filename(info_dict['title'])}"
                )
                audio_path = f"{base_path}.mp3"
                thumbnail_path = f"{base_path}.jpg"

                if not await aios.path.exists(thumbnail_path):
                    thumbnail_path = f"{base_path}.webp"

                await loop.run_in_executor(
                    self._download_executor,
                    lambda: update_metadata(
                        audio_path,
                        title=info_dict.get("title", "audio"),
                        artist=info_dict.get("uploader", "unknown"),
                        cover_file=thumbnail_path
                    )
                )

                return [{
                    "type": "audio",
                    "path": audio_path,
                    "cover": thumbnail_path
                }]

        except Exception as e:
            logging.error(f"YouTube audio error: {str(e)}", exc_info=True)
            return [{
                "type": "error",
                "message": e
            }]


def check_video_size(url, max_size_mb=50):
    ydl_opts = {
        'skip_download': True,
        'force_ipv4': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get('formats', [])
    suitable_formats = []

    for f in formats:
        ext = f.get('ext')
        vcodec = f.get('vcodec', '')
        filesize = f.get('filesize') or f.get('filesize_approx')  # На всякий случай

        if not filesize or ext != 'mp4' or not vcodec.startswith('avc1'):
            continue

        size_mb = filesize / (1024 * 1024)
        if size_mb <= max_size_mb:
            suitable_formats.append(f)

    if suitable_formats:
        best_format = max(
            suitable_formats,
            key=lambda x: (
                x.get('height', 0),
                x.get('tbr', 0)
            )
        )
        return True, best_format
    else:
        return False, None

# import logging
# import os
# import asyncio
# import re

# import yt_dlp
# from yt_dlp.utils import sanitize_filename

# from utils import update_metadata, get_all_tracks_from_playlist_soundcloud, truncate_string
# from aiogram.enums import InputMediaType
# from aiogram.types import FSInputFile
# from aiogram.utils.media_group import MediaGroupBuilder


# class YouTubeDownloader:
#     def __init__(self, output_path: str = "other/downloadsTemp"):
#         """
#         Initialize the YouTubeDownloader with an output path for downloads.

#         Parameters:
#         ----------
#         output_path : str, optional
#             The directory where downloaded files will be saved (default is "other/downloadsTemp").
#         """
#         self.output_path = output_path
#         os.makedirs(self.output_path, exist_ok=True)
#         self.yt_dlp_video_options = {
#                 "format": "bv*[filesize < 50M][ext=mp4][vcodec^=avc1] + ba[ext=m4a]",
#                 "outtmpl": f"{self.output_path}/%(title)s.%(ext)s",
#                 'noplaylist': True,
#             }
#         self.yt_dlp_audio_options = {
#                 "format": "m4a/bestaudio/best",
#                 "writethumbnail": True,
#                 "outtmpl": f"{self.output_path}/{sanitize_filename('%(title)s')}",
#                 "postprocessors": [
#                     {
#                         "key": "FFmpegExtractAudio",
#                         "preferredcodec": "mp3",
#                     }
#                 ],
#             }

#     async def download(self, url: str, format: str):
#         """
#         Download a media file (video or audio) based on the format.

#         Parameters:
#         ----------
#         url : str
#             The YouTube video URL to download.
#         format : str
#             The format of the download ('media' for video or 'audio' for audio).

#         Yields:
#         -------
#         AsyncGenerator
#             Returns an async generator yielding video, audio and cover filenames or None if an error occurs.
#         """
#         try:
#             if format == "media":
#                 async for result in self._download_video(url):
#                     yield result
#             elif format == "audio":
#                 if re.match(r"https://music\.youtube\.com/playlist\?list=([a-zA-Z0-9\-_]+)", url):
#                     # Playlist
#                     async for result in self._download_playlist(url):
#                         yield result

#                 #single track
#                 async for result in self._download_single_track(url):
#                     yield result
#             else:
#                 logging.error(f"Unsupported format: {format}")
#                 yield None
#         except Exception as e:
#             logging.error(f"Unexpected error: {e}")
#             yield None

#     async def _download_video(self, url: str):
#         """
#         Download a video from YouTube.

#         Parameters:
#         ----------
#         url : str
#             The YouTube video URL to download.

#         Yields:
#         -------
#         tuple
#             Yields a tuple containing the MediaGroup object, video title, and list of filenames
#         """
#         try:
#             with yt_dlp.YoutubeDL(self.yt_dlp_video_options) as ydl:
#                 info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
#                 title = info_dict.get("title", "video")
#                 filename = ydl.prepare_filename(info_dict)

#                 await asyncio.to_thread(ydl.download, [url])

#                 media_group = MediaGroupBuilder(caption=truncate_string(title))
#                 media_group.add_video(media=FSInputFile(filename), type=InputMediaType.VIDEO)

#                 if os.path.exists(filename):
#                     yield media_group, [filename]
#         except Exception as e:
#             logging.error(f"Error downloading YouTube video: {str(e)}")
#             yield None, None

#     async def _download_single_track(self, url: str):
#         """
#         Downloads a single SoundCloud track.

#         Parameters:
#         ----------
#         url : str
#             The URL of the SoundCloud track to download.

#         Yields:
#         -------
#         tuple
#             Yields the file paths of the downloaded audio and cover image, or None if an error occurs.
#         """
#         yield await self._download_track(url)

#     # async def _download_playlist(self, url: str):
#     #     """
#     #     Downloads a SoundCloud playlist by iterating over each track in the playlist.

#     #     Parameters:
#     #     ----------
#     #     url : str
#     #         The URL of the SoundCloud playlist to download.

#     #     Yields:
#     #     -------
#     #     tuple
#     #         Yields the file paths of the downloaded audio and cover image for each track, or None if an error occurs.
#     #     """
#     #     tracks = get_all_tracks_from_playlist_soundcloud(url)
#     #     for track in tracks:
#     #         yield await self._download_track(track)

#     async def _download_track(self, url: str):
#         """
#         Download audio from YouTube.

#         Parameters:
#         ----------
#         url : str
#             The YouTube video URL to download.

#         Yields:
#         -------
#         tuple
#             Yields a tuple containing the audio filename and thumbnail filename
#         """
#         try:
#             with yt_dlp.YoutubeDL(self.yt_dlp_audio_options) as ydl:
#                 info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
#                 title = info_dict.get("title", "audio")
#                 author = info_dict.get("uploader", "unknown")

#                 audio_filename = os.path.join(self.output_path, f"{sanitize_filename(title)}.mp3")
#                 thumbnail_filename = os.path.join(self.output_path, f"{sanitize_filename(title)}.webp")

#                 await asyncio.to_thread(ydl.download, [url])

#                 update_metadata(audio_filename, title=title, artist=author)

#                 if os.path.exists(audio_filename):
#                     return audio_filename, thumbnail_filename
#         except Exception as e:
#             logging.error(f"Error downloading YouTube Audio: {str(e)}")
#             return None, None
