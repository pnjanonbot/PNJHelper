import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import logging

from config.settings import BOT_TOKEN, ADMIN_USER_ID, CHAT_TIMEOUT
from models.chat_manager import ChatManager
from utils.helpers import create_stop_chat_keyboard, format_chat_ended_message
from handlers.command_handlers import (
    handle_start_command, 
    handle_queue_command, 
    handle_chat_command, 
    handle_stop_command,
    handle_help_command
)
from handlers.message_handlers import handle_message
from handlers.callback_handlers import handle_callback_query

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize chat manager
chat_manager = ChatManager(chat_timeout=CHAT_TIMEOUT)

async def start_chat_with_user(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Start a chat session with a user"""
    chat_manager.start_chat(user_id, ADMIN_USER_ID)

    keyboard = create_stop_chat_keyboard()
    
    try:
        await context.bot.send_message(
            chat_id=user_id, 
            text="Kamu sekarang terhubung dengan admin. Silakan kirim pesan.", 
            reply_markup=keyboard
        )
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID, 
            text=f"User {user_id} sekarang terhubung. Obrolan dimulai."
        )
        logger.info(f"Chat started between user {user_id} and admin.")

        # Start timeout checker
        await chat_manager.start_timeout_task(user_id, ADMIN_USER_ID, end_chat_callback)
    except Exception as e:
        logger.error(f"Failed to start chat with user {user_id}: {e}")


async def end_chat_callback(user_id: int, admin_id: int):
    """Callback function when chat times out"""
    await end_chat(user_id, admin_id, None)


async def end_chat(user_id: int, admin_id: int, context: ContextTypes.DEFAULT_TYPE):
    """End a chat session"""
    chat_manager.end_chat(user_id, admin_id)
    
    if context:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"Obrolan dengan user {user_id} telah berakhir.")
            await context.bot.send_message(chat_id=user_id, text=format_chat_ended_message())
        except Exception as e:
            logger.error(f"Failed to send end chat messages: {e}")
    
    logger.info(f"Chat ended between user {user_id} and admin.")

    # Start next chat if available
    next_user_id = chat_manager.get_next_user_in_queue()
    if next_user_id and not chat_manager.is_user_in_active_chat(admin_id):
        if context:
            await start_chat_with_user(next_user_id, context)


async def handle_stop_command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper for stop command that handles the actual chat ending"""
    user_id = update.effective_user.id
    if (chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID or 
        chat_manager.get_active_chat_partner(ADMIN_USER_ID) == user_id):
        await end_chat(user_id, ADMIN_USER_ID, context)
        if update.message:
            await update.message.reply_text("Obrolan telah diakhiri.")
    else:
        if update.message:
            await update.message.reply_text("Kamu tidak sedang dalam sesi obrolan.")


async def handle_callback_query_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper for callback query handling"""
    query = update.callback_query
    await query.answer()

    if query.data == "stop_chat":
        user_id = query.from_user.id
        if (chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID or 
            chat_manager.get_active_chat_partner(ADMIN_USER_ID) == user_id):
            await end_chat(user_id, ADMIN_USER_ID, context)
            await query.edit_message_text(text=format_chat_ended_message())
        else:
            await query.edit_message_text(text="Kamu tidak sedang dalam sesi obrolan.")


async def handle_message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper for message handling that includes chat timeout reset"""
    user_id = update.effective_user.id
    
    # If user is in active chat with admin, forward message to admin
    if chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID:
        try:
            await context.bot.copy_message(chat_id=ADMIN_USER_ID, from_chat_id=user_id, message_id=update.message.message_id)
            logger.info(f"Forwarded message from user {user_id} to admin.")
            
            # Reset timeout
            chat_manager.cancel_timeout_task(user_id)
            await chat_manager.start_timeout_task(user_id, ADMIN_USER_ID, end_chat_callback)
        except Exception as e:
            logger.error(f"Failed to forward message from user {user_id} to admin: {e}")
            if update.message:
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
                await chat_manager.start_timeout_task(user_in_chat, ADMIN_USER_ID, end_chat_callback)
            except Exception as e:
                logger.error(f"Failed to forward message from admin to user {user_in_chat}: {e}")
                if update.message:
                    await update.message.reply_text(f"Gagal mengirim pesan: {e}")
        return

    # If user is not in chat, direct them to use /chat command
    if user_id != ADMIN_USER_ID:
        if update.message:
            await update.message.reply_text("Gunakan /chat untuk meminta obrolan dengan admin.")


def main():
    logger.info("Bot is starting...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        logger.info("Application built successfully.")
    except Exception as e:
        logger.error(f"Failed to build application: {e}")
        print(f"Error: {e}")
        return

    # Add handlers
    application.add_handler(CommandHandler("start", lambda u, c: handle_start_command(u, c, chat_manager)))
    application.add_handler(CommandHandler("queue", lambda u, c: handle_queue_command(u, c, chat_manager)))
    application.add_handler(CommandHandler("chat", lambda u, c: handle_chat_command(u, c, chat_manager)))
    application.add_handler(CommandHandler("stop", handle_stop_command_wrapper))
    application.add_handler(CommandHandler("help", handle_help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_wrapper))
    application.add_handler(CallbackQueryHandler(handle_callback_query_wrapper))

    logger.info("Handlers added. Starting polling...")
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Error during polling: {e}")
        print(f"Polling error: {e}")

if __name__ == "__main__":
    main()