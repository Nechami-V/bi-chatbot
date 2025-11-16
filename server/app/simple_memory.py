"""
Simple Session Memory for OpenAI Context

Ultra-simple conversation memory using just Python dict.
No files, no complexity, just the last few messages per user.

Author: BI Chatbot Team  
Version: KISS (Keep It Simple Stupid)
"""
from typing import List, Dict, Any
from threading import Lock
import time

class SimpleSessionMemory:
    """Dead simple session memory"""
    
    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
    
    def add_exchange(self, user_id: str, question: str, answer: str):
        """Add Q&A pair to user session"""
        with self._lock:
            if user_id not in self._sessions:
                self._sessions[user_id] = []
            
            # Add both question and answer
            self._sessions[user_id].extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ])
            
            # Keep only last 4 messages (2 exchanges)
            if len(self._sessions[user_id]) > 4:
                self._sessions[user_id] = self._sessions[user_id][-4:]
            
            self._maybe_cleanup()
    
    def get_context_messages(self, user_id: str) -> List[Dict[str, str]]:
        """Get recent messages for OpenAI context (legacy method)"""
        with self._lock:
            return self._sessions.get(user_id, []).copy()
    
    def get_context_text(self, user_id: str) -> str:
        """Get recent conversation context as simple text for prompt injection"""
        with self._lock:
            messages = self._sessions.get(user_id, [])
            if not messages:
                return ""
            
            context_parts = []
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    question = messages[i]["content"]
                    answer = messages[i + 1]["content"]
                    context_parts.append(f"Previous Q: {question}")
                    context_parts.append(f"Previous A: {answer}")
            
            if context_parts:
                return "\n\nRecent conversation context:\n" + "\n".join(context_parts) + "\n"
            return ""
    
    def clear_user(self, user_id: str):
        """Clear specific user session"""
        with self._lock:
            self._sessions.pop(user_id, None)
    
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

# Global instance
session_memory = SimpleSessionMemory()