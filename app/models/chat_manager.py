from collections import deque
from datetime import datetime
from typing import Dict, Optional
import asyncio

class ChatManager:
    def __init__(self, max_queue_size: int = 10, chat_timeout: int = 300):
        self.user_queue = deque()
        self.active_chats = {}
        self.chat_start_times = {}
        self.timeout_tasks = {}
        self.max_queue_size = max_queue_size
        self.chat_timeout = chat_timeout

    def add_user_to_queue(self, user_id: int) -> bool:
        """Add user to queue if not already in queue or active chat"""
        if user_id in self.active_chats:
            return False
        if user_id in self.user_queue:
            return False
        if len(self.user_queue) >= self.max_queue_size:
            return False
        self.user_queue.append(user_id)
        return True

    def get_user_queue_position(self, user_id: int) -> Optional[int]:
        """Get user's position in queue (1-indexed), or None if not in queue"""
        if user_id in self.user_queue:
            return self.user_queue.index(user_id) + 1
        return None

    def is_user_in_queue(self, user_id: int) -> bool:
        """Check if user is in queue"""
        return user_id in self.user_queue

    def is_user_in_active_chat(self, user_id: int) -> bool:
        """Check if user is in active chat"""
        return user_id in self.active_chats

    def start_chat(self, user_id: int, admin_id: int):
        """Start a chat session between user and admin"""
        if user_id in self.user_queue:
            self.user_queue.remove(user_id)
        self.active_chats[user_id] = admin_id
        self.active_chats[admin_id] = user_id
        self.chat_start_times[user_id] = datetime.now()

    def end_chat(self, user_id: int, admin_id: int):
        """End a chat session"""
        self.active_chats.pop(user_id, None)
        self.active_chats.pop(admin_id, None)
        self.chat_start_times.pop(user_id, None)
        
        # Cancel timeout task if exists
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
            del self.timeout_tasks[user_id]

    def get_next_user_in_queue(self) -> Optional[int]:
        """Get the next user in queue"""
        if self.user_queue:
            return self.user_queue[0]
        return None

    def start_timeout_task(self, user_id: int, admin_id: int, callback):
        """Start a timeout task for a chat session"""
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
        self.timeout_tasks[user_id] = asyncio.create_task(
            self._timeout_task(user_id, admin_id, callback)
        )

    async def _timeout_task(self, user_id: int, admin_id: int, callback):
        """Internal timeout task"""
        try:
            await asyncio.sleep(self.chat_timeout)
            if self.active_chats.get(user_id) == admin_id:
                await callback(user_id, admin_id)
        except asyncio.CancelledError:
            pass

    def cancel_timeout_task(self, user_id: int):
        """Cancel timeout task for a user"""
        if user_id in self.timeout_tasks:
            self.timeout_tasks[user_id].cancel()
            del self.timeout_tasks[user_id]

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.user_queue)

    def get_active_chat_partner(self, user_id: int) -> Optional[int]:
        """Get the chat partner for a user"""
        return self.active_chats.get(user_id)

    def get_chat_duration(self, user_id: int) -> Optional[float]:
        """Get duration of current chat in seconds"""
        if user_id in self.chat_start_times:
            start_time = self.chat_start_times[user_id]
            return (datetime.now() - start_time).total_seconds()
        return None