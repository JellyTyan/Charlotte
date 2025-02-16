import asyncio
from typing import Optional

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from filters.url_filter import UrlFilter
from loader import dp
from utils import get_service_handler, handle_download_error
from managers.download_manager import TaskManager, MediaHandler, user_tasks


@dp.message(UrlFilter())
async def url_handler(message: types.Message) -> None:
    """Handle incoming URL messages and manage downloads."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    if await TaskManager().is_user_downloading(user_id, message):
        return

    url = message.text
    service = get_service_handler(url)

    if service.name == "Youtube":
        markup = InlineKeyboardBuilder()
        markup.add(types.InlineKeyboardButton(text=_("Video"), callback_data="video"))
        markup.add(types.InlineKeyboardButton(text=_("Audio"), callback_data="audio"))

        await message.reply(_("Choose a format to download:"), reply_markup=markup.as_markup())
    else:
        if service.is_playlist(url):
            task = asyncio.create_task(handle_playlist_download(service, url, message))
        else:
            task = asyncio.create_task(handle_single_download(service, url, message))

        TaskManager().add_task(user_id, task)


@dp.callback_query()
async def format_choice_handler(callback_query: types.CallbackQuery):
    choice = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    if not isinstance(message, types.Message):
        return

    assert message.reply_to_message, "Message is not reply"
    url = message.reply_to_message.text
    assert url, "URL is not found"

    service = get_service_handler(url)

    if service.name != "Youtube":
        await message.edit_text(_("The selection format is only available for YouTube."))
        return

    if choice == "video":
        task = asyncio.create_task(handle_single_download(service, url, message, format_choice=f"video:{user_id}"))
    elif choice == "audio":
        task = asyncio.create_task(handle_single_download(service, url, message, format_choice=f"audio:{user_id}"))
    else:
        await message.edit_text(_("Invalid choice."))
        return

    TaskManager().add_task(user_id, task)
    await message.delete()


async def handle_single_download(service, url: str, message: types.Message, format_choice: Optional[str] = None) -> None:
    """Handle download of a single media item."""
    user_id = 0
    assert message.bot, "Bot is not found"

    try:
        if service.name == "Youtube" and format_choice:
            format, user_id = format_choice.split(":")
            content = await service.download(url, format)
        else:
            await message.bot.send_chat_action(message.chat.id, "record_video")
            user_id = message.from_user.id
            content = await service.download(url)

        if not content:
            raise ValueError("Downloaded content is empty.")

        await MediaHandler.send_media_content(message, content)

    except Exception as e:
        await handle_download_error(message, e)

    finally:
        TaskManager().remove_task(int(user_id))


async def handle_playlist_download(service, url: str, message: types.Message) -> None:
    """Handle download of a playlist."""
    assert message.bot, "Bot is not found"

    try:
        tracks = service.get_playlist_tracks(url)
        for track in tracks:
            if message.from_user.id not in user_tasks:
                break

            try:
                await message.bot.send_chat_action(message.chat.id, "record_voice")
                file = await service.download(track)
                await MediaHandler.send_audio(message, file[0])
            except Exception:
                continue

        await message.reply(_("Download completed."))
    except Exception as e:
        await handle_download_error(message, e)
    finally:
        TaskManager().remove_task(message.from_user.id)
