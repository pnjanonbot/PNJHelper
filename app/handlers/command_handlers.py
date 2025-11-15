from telegram import Update
from telegram.ext import ContextTypes
from config.settings import ADMIN_USER_ID
from models.chat_manager import ChatManager
from utils.helpers import format_queue_message, format_max_queue_message
import logging

logger = logging.getLogger(__name__)


async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    user_id = update.effective_user.id
    logger.info(f"Received /start from user {user_id}")
    await update.message.reply_text(
        "Halo! Gunakan /chat untuk meminta obrolan dengan admin."
    )


async def handle_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admin tidak bisa menggunakan perintah ini.")
        return

    if chat_manager.is_user_in_active_chat(user_id):
        await update.message.reply_text("Kamu sedang dalam sesi obrolan. Gunakan /stop untuk mengakhiri.")
        return

    queue_position = chat_manager.get_user_queue_position(user_id)
    
    if queue_position:
        total_in_queue = chat_manager.get_queue_size()
        message = format_queue_message(user_id, queue_position, total_in_queue)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Kamu tidak ada dalam antrian saat ini.")


async def handle_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    user_id = update.effective_user.id
    logger.info(f"Received /chat from user {user_id}")
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admin tidak bisa menggunakan perintah ini.")
        return

    if chat_manager.is_user_in_active_chat(user_id):
        await update.message.reply_text("Kamu sedang dalam sesi obrolan. Gunakan /stop untuk mengakhiri.")
        return

    queue_position = chat_manager.get_user_queue_position(user_id)
    if queue_position:
        total_in_queue = chat_manager.get_queue_size()
        message = format_queue_message(user_id, queue_position, total_in_queue)
        await update.message.reply_text(message)
        return

    # Check if queue is full
    if chat_manager.get_queue_size() >= chat_manager.max_queue_size:
        await update.message.reply_text(format_max_queue_message(chat_manager.max_queue_size))
        return

    # Add user to queue
    success = chat_manager.add_user_to_queue(user_id)
    if not success:
        await update.message.reply_text("Terjadi kesalahan saat memasukkan kamu ke antrian.")
        return

    queue_position = chat_manager.get_user_queue_position(user_id)
    total_in_queue = chat_manager.get_queue_size()

    await update.message.reply_text(
        f"Kamu telah masuk dalam antrian. Kamu di posisi #{queue_position} dari {total_in_queue}. Mohon menunggu."
    )

    # If user is first in queue and admin is not in chat, start the chat
    if queue_position == 1 and not chat_manager.is_user_in_active_chat(ADMIN_USER_ID):
        # This will be handled by the main bot logic when the first user is processed
        pass


async def handle_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_manager: ChatManager):
    user_id = update.effective_user.id
    logger.info(f"Received /stop from user {user_id}")
    if (chat_manager.get_active_chat_partner(user_id) == ADMIN_USER_ID or 
        chat_manager.get_active_chat_partner(ADMIN_USER_ID) == user_id):
        # This will be handled by the main bot logic
        pass
    else:
        await update.message.reply_text("Kamu tidak sedang dalam sesi obrolan.")


async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Perintah yang tersedia:
/start - Memulai bot
/chat - Bergabung dalam antrian untuk berbicara dengan admin
/queue - Melihat posisi kamu dalam antrian
/stop - Mengakhiri sesi obrolan saat ini
/help - Menampilkan pesan bantuan ini
    """
    await update.message.reply_text(help_text)