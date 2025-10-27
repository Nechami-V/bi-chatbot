"""
Simple Conversation History for Natural Context

This module provides lightweight conversation history storage,
replacing the complex follow-up detection with OpenAI's natural understanding.

Features:
- Per-user conversation history (last N messages)
- Automatic TTL cleanup (30 minutes)
- Simple append-only storage
- Natural context for OpenAI

Author: BI Chatbot Team
Version: 2.0.0
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single conversation turn (question + answer)"""
    timestamp: datetime
    question: str
    answer: str
    sql_query: Optional[str] = None


class ConversationHistory:
    """
    Simple conversation history storage
    
    Stores last N conversation turns per user for natural context.
    OpenAI handles follow-up detection automatically.
    """
    
    def __init__(self, max_turns: int = 3, ttl_minutes: int = 30):
        """
        Initialize conversation history
        
        Args:
            max_turns: Maximum conversation turns to keep per user
            ttl_minutes: Time-to-live for conversations in minutes
        """
        self.max_turns = max_turns
        self.ttl_minutes = ttl_minutes
        self._conversations: Dict[str, List[ConversationTurn]] = {}
        self._lock = Lock()
        
        logger.info(f"ConversationHistory initialized (max_turns={max_turns}, ttl={ttl_minutes}min)")

    def add_turn(self, user_id: str, question: str, answer: str, sql_query: Optional[str] = None):
        """
        Add a new conversation turn
        
        Args:
            user_id: User identifier
            question: User's question
            answer: System's answer
            sql_query: Optional SQL query that was executed
        """
        with self._lock:
            if user_id not in self._conversations:
                self._conversations[user_id] = []
            
            # Add new turn
            turn = ConversationTurn(
                timestamp=datetime.now(),
                question=question,
                answer=answer,
                sql_query=sql_query
            )
            
            self._conversations[user_id].append(turn)
            
            # Keep only last N turns
            if len(self._conversations[user_id]) > self.max_turns:
                self._conversations[user_id] = self._conversations[user_id][-self.max_turns:]
            
            logger.debug(f"Added conversation turn for user {user_id} (total: {len(self._conversations[user_id])})")

    def get_recent_history(self, user_id: str, limit: Optional[int] = None) -> List[ConversationTurn]:
        """
        Get recent conversation history for user
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of turns to return
            
        Returns:
            List of recent conversation turns (oldest first)
        """
        with self._lock:
            self._cleanup_expired()
            
            if user_id not in self._conversations:
                return []
            
            history = self._conversations[user_id]
            
            if limit:
                history = history[-limit:]
            
            logger.debug(f"Retrieved {len(history)} conversation turns for user {user_id}")
            return history

    def build_context_for_openai(self, user_id: str) -> List[Dict[str, str]]:
        """
        Build conversation context in OpenAI message format
        
        Args:
            user_id: User identifier
            
        Returns:
            List of messages in OpenAI format [{"role": "user/assistant", "content": "..."}]
        """
        history = self.get_recent_history(user_id, limit=2)  # Last 2 turns for context
        
        messages = []
        for turn in history:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})
        
        logger.debug(f"Built OpenAI context with {len(messages)} messages for user {user_id}")
        return messages

    def clear_user_history(self, user_id: str):
        """Clear conversation history for specific user"""
        with self._lock:
            if user_id in self._conversations:
                del self._conversations[user_id]
                logger.debug(f"Cleared conversation history for user {user_id}")

    def _cleanup_expired(self):
        """Remove expired conversations"""
        cutoff_time = datetime.now() - timedelta(minutes=self.ttl_minutes)
        
        expired_users = []
        for user_id, turns in self._conversations.items():
            # Filter out expired turns
            valid_turns = [turn for turn in turns if turn.timestamp > cutoff_time]
            
            if not valid_turns:
                expired_users.append(user_id)
            else:
                self._conversations[user_id] = valid_turns
        
        # Remove users with no valid turns
        for user_id in expired_users:
            del self._conversations[user_id]
        
        if expired_users:
            logger.debug(f"Cleaned up expired conversations for {len(expired_users)} users")

    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics"""
        with self._lock:
            self._cleanup_expired()
            
            total_users = len(self._conversations)
            total_turns = sum(len(turns) for turns in self._conversations.values())
            
            return {
                "active_users": total_users,
                "total_turns": total_turns,
                "max_turns_per_user": self.max_turns,
                "ttl_minutes": self.ttl_minutes
            }


# Global instance
conversation_history = ConversationHistory(max_turns=3, ttl_minutes=30)