"""
Context Memory for Single-Turn Follow-Up Detection

This module provides lightweight in-memory storage for the last user context,
enabling smart follow-up detection without maintaining full conversation history.

Features:
- Per-user context storage (keyed by user ID)
- TTL-based automatic cleanup (15 minutes)
- Minimal memory footprint
- Thread-safe operations

Author: BI Chatbot Team
Version: 1.0.0
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """Single-turn context for a user"""
    prev_question: str
    prev_answer_summary: str  # 1 short sentence in Hebrew
    prev_sql_snippet: Optional[str]  # Truncated to ~300 chars
    updated_at: datetime
    
    def is_expired(self, ttl_minutes: int = 15) -> bool:
        """Check if context has expired based on TTL"""
        age = datetime.now() - self.updated_at
        return age > timedelta(minutes=ttl_minutes)


class ContextMemoryStore:
    """
    In-memory store for user contexts with TTL-based cleanup.
    Thread-safe for concurrent access.
    """
    
    def __init__(self, ttl_minutes: int = 15):
        """
        Initialize context memory store.
        
        Args:
            ttl_minutes: Time-to-live in minutes for context entries
        """
        self._storage: Dict[int, UserContext] = {}
        self._lock = Lock()
        self._ttl_minutes = ttl_minutes
        logger.info(f"Initialized ContextMemoryStore with TTL={ttl_minutes} minutes")
    
    def get(self, user_id: int) -> Optional[UserContext]:
        """
        Retrieve user context and clean up expired entries.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserContext if exists and not expired, None otherwise
        """
        with self._lock:
            # Cleanup expired entries first
            self._cleanup_expired()
            
            context = self._storage.get(user_id)
            
            if context is None:
                logger.debug(f"No context found for user {user_id}")
                return None
            
            if context.is_expired(self._ttl_minutes):
                logger.debug(f"Context expired for user {user_id}, removing")
                del self._storage[user_id]
                return None
            
            logger.debug(f"Retrieved context for user {user_id}")
            return context
    
    def set(
        self,
        user_id: int,
        question: str,
        answer_summary: str,
        sql_snippet: Optional[str] = None
    ) -> None:
        """
        Store or update user context.
        
        Args:
            user_id: Unique user identifier
            question: Current question (will become prev_question)
            answer_summary: Short 1-sentence summary in Hebrew
            sql_snippet: Optional SQL query, truncated to ~300 chars
        """
        with self._lock:
            # Truncate SQL if needed
            if sql_snippet and len(sql_snippet) > 300:
                sql_snippet = sql_snippet[:297] + "..."
            
            context = UserContext(
                prev_question=question,
                prev_answer_summary=answer_summary,
                prev_sql_snippet=sql_snippet,
                updated_at=datetime.now()
            )
            
            self._storage[user_id] = context
            logger.debug(f"Updated context for user {user_id}")
    
    def clear(self, user_id: int) -> None:
        """
        Clear context for a specific user.
        
        Args:
            user_id: Unique user identifier
        """
        with self._lock:
            if user_id in self._storage:
                del self._storage[user_id]
                logger.debug(f"Cleared context for user {user_id}")
    
    def _cleanup_expired(self) -> None:
        """Remove all expired contexts (called internally with lock held)"""
        expired_users = [
            uid for uid, ctx in self._storage.items()
            if ctx.is_expired(self._ttl_minutes)
        ]
        
        for uid in expired_users:
            del self._storage[uid]
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired contexts")
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics for monitoring"""
        with self._lock:
            self._cleanup_expired()
            return {
                "total_contexts": len(self._storage),
                "ttl_minutes": self._ttl_minutes
            }
