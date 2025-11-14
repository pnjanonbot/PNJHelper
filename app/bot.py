import os
import asyncio
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
if not ADMIN_USER_ID:
    raise ValueError("ADMIN_USER_ID is not set in .env")

user_queue = deque()
active_chats = {}
chat_start_times = {}
timeout_tasks = {}

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Received /start from user {user_id}")
    await update.message.reply_text(
        "Halo! Gunakan /chat untuk meminta obrolan dengan admin."
    )

async def handle_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admin tidak bisa menggunakan perintah ini.")
        return

    if user_id in active_chats:
        await update.message.reply_text("Kamu sedang dalam sesi obrolan. Gunakan /stop untuk mengakhiri.")
        return

    queue_position = None
    if user_id in user_queue:
        queue_position = user_queue.index(user_id) + 1

    if queue_position:
        total_in_queue = len(user_queue)
        await update.message.reply_text(f"Kamu saat ini di posisi #{queue_position} dari {total_in_queue} antrian.")
    else:
        await update.message.reply_text("Kamu tidak ada dalam antrian saat ini.")

async def handle_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Received /chat from user {user_id}")
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admin tidak bisa menggunakan perintah ini.")
        return

    if user_id in active_chats:
        await update.message.reply_text("Kamu sedang dalam sesi obrolan. Gunakan /stop untuk mengakhiri.")
        return

    if user_id in user_queue:
        queue_position = user_queue.index(user_id) + 1
        total_in_queue = len(user_queue)
        await update.message.reply_text(f"Kamu sudah ada dalam antrian di posisi #{queue_position} dari {total_in_queue}. Mohon bersabar.")
        return

    user_queue.append(user_id)

    queue_position = len(user_queue)
    total_in_queue = queue_position

    if queue_position == 1 and ADMIN_USER_ID not in active_chats:
        await start_chat_with_user(update, context, user_id)
    else:
        await update.message.reply_text(
            f"Kamu telah masuk dalam antrian. Kamu di posisi #{queue_position} dari {total_in_queue}. Mohon menunggu."
        )
        if queue_position == 2:
            next_user_id = user_queue[0]
            if next_user_id != user_id:
                try:
                    await context.bot.send_message(chat_id=next_user_id, text="Giliranmu hampir tiba. Bersiaplah untuk obrolan.")
                except Exception as e:
                    logger.error(f"Failed to send notification to user {next_user_id}: {e}")

async def start_chat_with_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    user_queue.popleft()
    active_chats[user_id] = ADMIN_USER_ID
    active_chats[ADMIN_USER_ID] = user_id
    chat_start_times[user_id] = datetime.now()

    keyboard = [[InlineKeyboardButton("❌ Akhiri Obrolan", callback_data="stop_chat")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update:
        await update.message.reply_text("Kamu sekarang terhubung dengan admin. Silakan kirim pesan.", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=user_id, text="Kamu sekarang terhubung dengan admin. Silakan kirim pesan.", reply_markup=reply_markup)

    await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f"User {user_id} sekarang terhubung. Obrolan dimulai.")
    logger.info(f"Chat started between user {user_id} and admin.")

    if user_id in timeout_tasks:
        timeout_tasks[user_id].cancel()
    timeout_tasks[user_id] = context.application.create_task(timeout_checker(user_id, context))

async def handle_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_id = ADMIN_USER_ID
    logger.info(f"Received /stop from user {user_id}")
    if active_chats.get(user_id) == admin_id or active_chats.get(admin_id) == user_id:
        await end_chat(user_id, admin_id, context)
    else:
        await update.message.reply_text("Kamu tidak sedang dalam sesi obrolan.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "stop_chat":
        user_id = query.from_user.id
        admin_id = ADMIN_USER_ID
        if active_chats.get(user_id) == admin_id or active_chats.get(admin_id) == user_id:
            await end_chat(user_id, admin_id, context)
            await query.edit_message_text(text="Obrolan telah berakhir. Terima kasih!")
        else:
            await query.edit_message_text(text="Kamu tidak sedang dalam sesi obrolan.")

async def end_chat(user_id: int, admin_id: int, context: ContextTypes.DEFAULT_TYPE):
    active_chats.pop(user_id, None)
    active_chats.pop(admin_id, None)
    chat_start_times.pop(user_id, None)
    if user_id in timeout_tasks:
        timeout_tasks[user_id].cancel()
        timeout_tasks.pop(user_id, None)

    await context.bot.send_message(chat_id=admin_id, text=f"Obrolan dengan user {user_id} telah berakhir.")
    await context.bot.send_message(chat_id=user_id, text="Obrolan telah berakhir. Terima kasih!")
    logger.info(f"Chat ended between user {user_id} and admin.")

    if user_queue:
        next_user_id = user_queue[0]
        await start_chat_with_user(None, context, next_user_id)

async def timeout_checker(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Timeout task started for user {user_id}, waiting 5 minutes.")
    try:
        await asyncio.sleep(300)
        if active_chats.get(user_id) == ADMIN_USER_ID:
            logger.info(f"Timeout reached for user {user_id}. Ending chat.")
            await end_chat(user_id, ADMIN_USER_ID, context)
    except asyncio.CancelledError:
        logger.info(f"Timeout task for user {user_id} was cancelled.")
        raise

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_id = ADMIN_USER_ID
    logger.info(f"Received message from user {user_id}")

    if active_chats.get(user_id) == admin_id:
        try:
            await context.bot.copy_message(chat_id=admin_id, from_chat_id=user_id, message_id=update.message.message_id)
            logger.info(f"Forwarded message from user {user_id} to admin.")
            if user_id in timeout_tasks:
                timeout_tasks[user_id].cancel()
            timeout_tasks[user_id] = context.application.create_task(timeout_checker(user_id, context))
        except Exception as e:
            logger.error(f"Failed to forward message from user {user_id} to admin: {e}")
            await update.message.reply_text(f"Gagal mengirim pesan: {e}")
        return

    if user_id == admin_id:
        user_in_chat = active_chats.get(admin_id)
        if user_in_chat:
            try:
                await context.bot.copy_message(chat_id=user_in_chat, from_chat_id=admin_id, message_id=update.message.message_id)
                logger.info(f"Forwarded message from admin to user {user_in_chat}.")
                if user_in_chat in timeout_tasks:
                    timeout_tasks[user_in_chat].cancel()
                timeout_tasks[user_in_chat] = context.application.create_task(timeout_checker(user_in_chat, context))
            except Exception as e:
                logger.error(f"Failed to forward message from admin to user {user_in_chat}: {e}")
                await update.message.reply_text(f"Gagal mengirim pesan: {e}")
        return

    if user_id != admin_id:
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

    application.add_handler(CommandHandler("start", handle_start_command))
    application.add_handler(CommandHandler("chat", handle_chat_command))
    application.add_handler(CommandHandler("queue", handle_queue_command))
    application.add_handler(CommandHandler("stop", handle_stop_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    logger.info("Handlers added. Starting polling...")
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Error during polling: {e}")
        print(f"Polling error: {e}")

if __name__ == "__main__":
    main()
