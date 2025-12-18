"""
Simple Session Memory for OpenAI Context

Ultra-simple conversation memory using just Python dict.
No files, no complexity, just the last few messages per user.

Author: BI Chatbot Team  
Version: KISS (Keep It Simple Stupid)
"""
from typing import List, Dict, Any, Optional
from threading import Lock
import time

MAX_MESSAGES_PER_SESSION: Optional[int] = None  # None = שמירת כל השיחה עד איפוס יזום


class SimpleSessionMemory:
    """זיכרון שיחה בסיסי הנשמר בזיכרון בלבד"""

    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
    
    def add_exchange(self, user_id: str, question: str, answer: str, sql: Optional[str] = None):
        """Add Q&A pair to user session, optionally storing the SQL that produced the answer."""
        with self._lock:
            user_key = str(user_id)
            if user_key not in self._sessions:
                self._sessions[user_key] = []
            
            # Add both question and answer
            self._sessions[user_key].extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer, "sql": sql}
            ])
            
            if MAX_MESSAGES_PER_SESSION and len(self._sessions[user_key]) > MAX_MESSAGES_PER_SESSION:
                self._sessions[user_key] = self._sessions[user_key][-MAX_MESSAGES_PER_SESSION:]
            
            self._maybe_cleanup()
    
    def get_context_text(self, user_id: str) -> str:
        """Get recent conversation context as simple text for prompt injection"""
        with self._lock:
            user_key = str(user_id)
            messages = self._sessions.get(user_key, [])
            if not messages:
                return ""
            
            context_parts = []
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    question = messages[i]["content"]
                    answer = messages[i + 1]["content"]
                    context_parts.append(f"Previous Q: {question}")
                    context_parts.append(f"Previous A: {answer}")
                    sql = messages[i + 1].get("sql")
                    if sql:
                        context_parts.append(f"SQL used: {sql}")
            
            if context_parts:
                return "\n\nRecent conversation context:\n" + "\n".join(context_parts) + "\n"
            return ""
    
    def _maybe_cleanup(self):
        """Clean old sessions every 10 minutes"""
        now = time.time()
        if now - self._last_cleanup > 600:  # 10 minutes
            # In real app, would check timestamps, but for simplicity just limit total users
            if len(self._sessions) > 100:
                # Keep only 50 most recent users (simple cleanup)
                user_ids = list(self._sessions.keys())
                for old_user in user_ids[:-50]:
                    del self._sessions[old_user]
            
            self._last_cleanup = now

    def reset_session(self, user_id: str) -> None:
        """איפוס יזום של ההיסטוריה למשתמש – למשל בעת פתיחת צ'אט חדש"""
        with self._lock:
            self._sessions.pop(str(user_id), None)

# Global instance
session_memory = SimpleSessionMemory()