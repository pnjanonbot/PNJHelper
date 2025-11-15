from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_USER_ID
from models.chat_manager import ChatManager
from utils.helpers import create_stop_chat_keyboard, format_chat_ended_message
import logging

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    query = update.callback_query
    await query.answer()

    if query.data == "stop_chat":
        user_id = query.from_user.id
        if (chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID or 
            chat_manager.get_active_chat_partner(ADMIN_USER_ID) == user_id):
            # End chat will be handled by main bot logic
            pass
        else:
            await query.edit_message_text(text="Kamu tidak sedang dalam sesi obrolan.")