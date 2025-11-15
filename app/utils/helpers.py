from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_stop_chat_keyboard():
    """Create inline keyboard with stop chat button"""
    keyboard = [[InlineKeyboardButton("❌ Akhiri Obrolan", callback_data="stop_chat")]]
    return InlineKeyboardMarkup(keyboard)


def format_queue_message(user_id: int, position: int, total_in_queue: int) -> str:
    """Format message for queue status"""
    if position == 1:
        return f"Kamu saat ini di posisi #{position} dari {total_in_queue} antrian. Kamu akan segera dihubungkan ke admin."
    else:
        return f"Kamu saat ini di posisi #{position} dari {total_in_queue} antrian. Mohon bersabar."


def format_chat_started_message(is_user: bool) -> str:
    """Format message when chat starts"""
    if is_user:
        return "Kamu sekarang terhubung dengan admin. Silakan kirim pesan."
    else:
        return "Obrolan telah dimulai. Silakan kirim pesan."


def format_chat_ended_message() -> str:
    """Format message when chat ends"""
    return "Obrolan telah berakhir. Terima kasih!"


def format_max_queue_message(max_size: int) -> str:
    """Format message when queue is full"""
    return f"Maaf, antrian sedang penuh (maksimal {max_size} pengguna). Silakan coba lagi nanti."