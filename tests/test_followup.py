"""
Tests for Follow-Up Detection and Context Memory

Tests the follow-up detection heuristics, answer summarization,
and TTL-based context memory management.

Author: BI Chatbot Team
Version: 1.0.0
"""
import pytest
import time
from datetime import datetime, timedelta

from app.followup import is_follow_up, summarize_answer, build_context_block
from app.context_memory import ContextMemoryStore, UserContext


class TestFollowUpDetection:
    """Tests for follow-up question detection heuristics"""
    
    def test_no_previous_question(self):
        """Test that no follow-up detected when there's no previous question"""
        assert is_follow_up("כמה לקוחות יש?", None) == False
    
    def test_short_query_is_followup(self):
        """Test that very short queries are detected as follow-ups"""
        prev = "כמה לקוחות יש?"
        assert is_follow_up("בירושלים", prev) == True
        assert is_follow_up("וגם בחיפה", prev) == True
        assert is_follow_up("עכשיו", prev) == True
    
    def test_followup_starters(self):
        """Test detection of follow-up starter words"""
        prev = "מה המכירות החודש?"
        
        # Hebrew follow-up starters
        assert is_follow_up("וגם השנה?", prev) == True
        assert is_follow_up("ומה בחודש הבא?", prev) == True
        assert is_follow_up("וכמה בשנה שעברה?", prev) == True
        assert is_follow_up("ובשנה הבאה?", prev) == True
        assert is_follow_up("ובחודש אפריל?", prev) == True
        assert is_follow_up("ואז מה?", prev) == True
        assert is_follow_up("גם בקיץ?", prev) == True
    
    def test_time_shift_without_entity(self):
        """Test detection of time-shift patterns without main entity"""
        prev = "כמה לקוחות יש לנו?"
        
        # Time shifts without restating "לקוח"
        assert is_follow_up("בחודש שעבר", prev) == True
        assert is_follow_up("בשנה הבאה", prev) == True
        assert is_follow_up("בשבוע האחרון", prev) == True
        assert is_follow_up("עכשיו", prev) == True
        assert is_follow_up("השנה", prev) == True
        
        # But NOT a follow-up if entity is restated
        assert is_follow_up("כמה לקוחות בחודש שעבר?", prev) == False
    
    def test_comparative_starters(self):
        """Test detection of comparative question starters"""
        prev = "מה המכירות בינואר?"
        
        assert is_follow_up("יותר מפברואר?", prev) == True
        assert is_follow_up("פחות מהשנה שעברה?", prev) == True
        assert is_follow_up("גבוה מהממוצע?", prev) == True
    
    def test_modifier_only_patterns(self):
        """Test detection of modifier-only questions"""
        prev = "כמה לקוחות יש?"
        
        assert is_follow_up("בירושלים", prev) == True
        assert is_follow_up("בחיפה", prev) == True
        assert is_follow_up("מהעיר", prev) == True
    
    def test_full_questions_not_followup(self):
        """Test that complete standalone questions are NOT detected as follow-ups"""
        prev = "כמה לקוחות יש בירושלים?"
        
        # These are complete questions with entities
        assert is_follow_up("מה המכירות החודש?", prev) == False
        assert is_follow_up("כמה לקוחות יש בחיפה?", prev) == False
        assert is_follow_up("איזה מוצרים נמכרו הכי הרבה?", prev) == False


class TestAnswerSummarization:
    """Tests for answer summarization"""
    
    def test_short_answer_unchanged(self):
        """Test that short answers are returned as-is"""
        answer = "יש 150 לקוחות בירושלים."
        summary = summarize_answer(answer, max_length=100)
        assert summary == "יש 150 לקוחות בירושלים"
    
    def test_first_sentence_extraction(self):
        """Test extraction of first sentence from multi-sentence answer"""
        answer = "יש 150 לקוחות בירושלים. זה יותר מאשר בחיפה. המגמה עולה."
        summary = summarize_answer(answer, max_length=100)
        assert "יש 150 לקוחות בירושלים" in summary
        assert "זה יותר מאשר בחיפה" not in summary
    
    def test_long_sentence_truncation(self):
        """Test truncation of very long sentences"""
        answer = "יש " + " ".join(["לקוח"] * 50) + " בעיר הזאת."
        summary = summarize_answer(answer, max_length=50)
        assert len(summary) <= 53  # 50 + "..."
        assert summary.endswith("...")
    
    def test_whitespace_normalization(self):
        """Test that extra whitespace is removed"""
        answer = "יש    150   לקוחות   בירושלים."
        summary = summarize_answer(answer)
        assert "  " not in summary
        assert summary == "יש 150 לקוחות בירושלים"
    
    def test_empty_answer(self):
        """Test handling of empty answer"""
        assert summarize_answer("") == ""
        assert summarize_answer("   ") == ""


class TestContextBlock:
    """Tests for context block building"""
    
    def test_basic_context_block(self):
        """Test building basic context block"""
        block = build_context_block(
            prev_question="כמה לקוחות יש?",
            prev_answer_summary="יש 150 לקוחות",
            prev_sql_snippet=None
        )
        
        assert "הקשר קודם:" in block
        assert "כמה לקוחות יש?" in block
        assert "יש 150 לקוחות" in block
    
    def test_context_block_with_sql(self):
        """Test building context block with SQL snippet"""
        block = build_context_block(
            prev_question="כמה לקוחות יש?",
            prev_answer_summary="יש 150 לקוחות",
            prev_sql_snippet="SELECT COUNT(*) FROM Clients"
        )
        
        assert "SQL קודם:" in block
        assert "SELECT COUNT(*) FROM Clients" in block


class TestContextMemoryStore:
    """Tests for context memory storage with TTL"""
    
    @pytest.fixture
    def store(self):
        """Create a fresh store for each test"""
        return ContextMemoryStore(ttl_minutes=15)
    
    def test_store_and_retrieve(self, store):
        """Test storing and retrieving context"""
        store.set(
            user_id=123,
            question="כמה לקוחות יש?",
            answer_summary="יש 150 לקוחות",
            sql_snippet="SELECT COUNT(*) FROM Clients"
        )
        
        context = store.get(123)
        assert context is not None
        assert context.prev_question == "כמה לקוחות יש?"
        assert context.prev_answer_summary == "יש 150 לקוחות"
        assert context.prev_sql_snippet == "SELECT COUNT(*) FROM Clients"
    
    def test_no_context_for_new_user(self, store):
        """Test that new users have no context"""
        context = store.get(999)
        assert context is None
    
    def test_sql_truncation(self, store):
        """Test that long SQL is truncated to 300 chars"""
        long_sql = "SELECT * FROM Clients WHERE " + " AND ".join([f"col{i} = {i}" for i in range(100)])
        
        store.set(
            user_id=123,
            question="test",
            answer_summary="test",
            sql_snippet=long_sql
        )
        
        context = store.get(123)
        assert len(context.prev_sql_snippet) <= 300
        assert context.prev_sql_snippet.endswith("...")
    
    def test_context_update(self, store):
        """Test updating existing context"""
        store.set(user_id=123, question="Q1", answer_summary="A1")
        store.set(user_id=123, question="Q2", answer_summary="A2")
        
        context = store.get(123)
        assert context.prev_question == "Q2"
        assert context.prev_answer_summary == "A2"
    
    def test_clear_context(self, store):
        """Test clearing user context"""
        store.set(user_id=123, question="test", answer_summary="test")
        assert store.get(123) is not None
        
        store.clear(123)
        assert store.get(123) is None
    
    def test_ttl_expiration(self):
        """Test that contexts expire after TTL"""
        # Create store with very short TTL
        store = ContextMemoryStore(ttl_minutes=0)  # Expires immediately
        
        store.set(user_id=123, question="test", answer_summary="test")
        
        # Wait a tiny bit
        time.sleep(0.1)
        
        # Should be expired
        context = store.get(123)
        assert context is None
    
    def test_ttl_not_expired(self, store):
        """Test that contexts within TTL are still available"""
        store.set(user_id=123, question="test", answer_summary="test")
        
        # Immediately retrieve (well within TTL)
        context = store.get(123)
        assert context is not None
    
    def test_multiple_users_independent(self, store):
        """Test that different users have independent contexts"""
        store.set(user_id=123, question="Q1", answer_summary="A1")
        store.set(user_id=456, question="Q2", answer_summary="A2")
        
        context1 = store.get(123)
        context2 = store.get(456)
        
        assert context1.prev_question == "Q1"
        assert context2.prev_question == "Q2"
        
        # Clearing one doesn't affect the other
        store.clear(123)
        assert store.get(123) is None
        assert store.get(456) is not None
    
    def test_get_stats(self, store):
        """Test storage statistics"""
        store.set(user_id=123, question="test", answer_summary="test")
        store.set(user_id=456, question="test", answer_summary="test")
        
        stats = store.get_stats()
        assert stats["total_contexts"] == 2
        assert stats["ttl_minutes"] == 15


class TestUserContext:
    """Tests for UserContext dataclass"""
    
    def test_is_expired_within_ttl(self):
        """Test that recent context is not expired"""
        context = UserContext(
            prev_question="test",
            prev_answer_summary="test",
            prev_sql_snippet=None,
            updated_at=datetime.now()
        )
        
        assert context.is_expired(ttl_minutes=15) == False
    
    def test_is_expired_after_ttl(self):
        """Test that old context is expired"""
        context = UserContext(
            prev_question="test",
            prev_answer_summary="test",
            prev_sql_snippet=None,
            updated_at=datetime.now() - timedelta(minutes=20)
        )
        
        assert context.is_expired(ttl_minutes=15) == True
    
    def test_is_expired_at_boundary(self):
        """Test expiration right at TTL boundary"""
        context = UserContext(
            prev_question="test",
            prev_answer_summary="test",
            prev_sql_snippet=None,
            updated_at=datetime.now() - timedelta(minutes=15, seconds=1)
        )
        
        assert context.is_expired(ttl_minutes=15) == True
