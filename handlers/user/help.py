from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from .url import TaskManager

from loader import dp


@dp.message(Command("help"))
async def help_command(message: types.Message, state: FSMContext) -> None:
    user = message.from_user
    if user is None:
        return

    await message.answer(
        _(
            "<b>Hey, {name}! You've reached out for help!</b>\n"
            "To get started, here are the commands available <i>to you</i>:\n"
            "<i>/start</i> - start using the bot\n"
            "<i>/help</i> - get a list of available commands\n"
            "<i>/settings</i> - bot settings\n\n"
            "<i>/support</i> - for support me :3\n\n"
            "But that's just the beginning! I download media for you from anywhere! (even BiliBili)\n\n"
            "Let me list all the available sources for you:\n"
            "<b>Youtube</b> - I'll download videos, shorts, or music from videos for you! There's a 50 MB limit per video.\n"
            "<b>Soundcloud</b> - I'll download music, add the cover, title, and artist to make it all look perfect!\n"
            "<b>Spotify</b> - Similar functionality to Soundcloud, but for Spotify!\n"
            "<b>Apple Music</b> - Same here! Only beauty!\n"
            "<b>TikTok</b> - I'll download videos and images for you!\n"
            "<b>Pinterest</b> - I can download videos and photos for you.\n"
            "<b>BiliBili</b> - It's a bit of a hassle, but I can send you videos.\n"
            "<b>Twitter</b> - I'll download videos and photos for you.\n"
            "<b>Instagram</b> - I'll download photos or Reels for you.\n"
            "<b>Pixiv</b> - I'll download artworks  for you.\n"
        ).format(name=user.first_name or user.username),
        parse_mode=ParseMode.HTML,
    )


@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext) -> None:
    user = message.from_user
    if user is None:
        return

    canceled = TaskManager().cancel_task(user.id)
    if canceled:
        await message.answer(_("Your download has been cancelled."))
    else:
        await message.answer(_("No active download task found to cancel."))
