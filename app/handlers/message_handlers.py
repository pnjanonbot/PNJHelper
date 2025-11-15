from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_USER_ID
from models.chat_manager import ChatManager
from utils.helpers import create_stop_chat_keyboard
import logging

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    user_id = update.effective_user.id
    logger.info(f"Received message from user {user_id}")

    # If user is in active chat with admin, forward message to admin
    if chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID:
        try:
            await context.bot.copy_message(chat_id=ADMIN_USER_ID, from_chat_id=user_id, message_id=update.message.message_id)
            logger.info(f"Forwarded message from user {user_id} to admin.")
            
            # Reset timeout
            chat_manager.cancel_timeout_task(user_id)
            await chat_manager.start_timeout_task(user_id, ADMIN_USER_ID, lambda u, a: None)  # Placeholder callback
        except Exception as e:
            logger.error(f"Failed to forward message from user {user_id} to admin: {e}")
            await update.message.reply_text(f"Gagal mengirim pesan: {e}")
        return

    # If admin is sending message, forward to user in active chat
    if user_id == ADMIN_USER_ID:
        user_in_chat = chat_manager.get_active_chat_partner(ADMIN_USER_ID)
        if user_in_chat:
            try:
                await context.bot.copy_message(chat_id=user_in_chat, from_chat_id=ADMIN_USER_ID, message_id=update.message.message_id)
                logger.info(f"Forwarded message from admin to user {user_in_chat}.")
                
                # Reset timeout for the user
                chat_manager.cancel_timeout_task(user_in_chat)
                await chat_manager.start_timeout_task(user_in_chat, ADMIN_USER_ID, lambda u, a: None)  # Placeholder callback
            except Exception as e:
                logger.error(f"Failed to forward message from admin to user {user_in_chat}: {e}")
                await update.message.reply_text(f"Gagal mengirim pesan: {e}")
        return

    # If user is not in chat, direct them to use /chat command
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Gunakan /chat untuk meminta obrolan dengan admin.")