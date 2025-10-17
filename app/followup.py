"""
Follow-Up Detection and Answer Summarization

This module provides smart follow-up detection for Hebrew BI queries
and automatic answer summarization for context preservation.

Features:
- Heuristic-based follow-up detection
- Hebrew-aware linguistic patterns
- Automatic answer summarization (1 sentence)
- Minimal token usage

Author: BI Chatbot Team
Version: 1.0.0
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def is_follow_up(question: str, prev_question: Optional[str]) -> bool:
    """
    Detect if current question is a follow-up to the previous question.
    
    Uses heuristics:
    - Very short queries (< 15 chars)
    - Elliptical queries (missing subject/verb)
    - Follow-up starters: ["וגם", "ומה", "וכמה", "ובחודש", "ובשנה", "ואז"]
    - Time-shift words without entity restatement
    
    Args:
        question: Current user question
        prev_question: Previous question (None if first question)
        
    Returns:
        True if likely a follow-up, False otherwise
    """
    if not prev_question:
        logger.debug("No previous question - not a follow-up")
        return False
    
    # Normalize whitespace
    question = question.strip()
    
    # Heuristic 1: Very short queries (likely elliptical)
    if len(question) < 15:
        logger.debug(f"Short query detected ({len(question)} chars) - likely follow-up")
        return True
    
    # Heuristic 2: Follow-up starters
    follow_up_starters = [
        "וגם", "ומה", "וכמה", "ובחודש", "ובשנה", "ואז",
        "ומי", "ואיך", "ולמה", "ומתי", "ואיפה",
        "גם", "נוסף", "בנוסף"
    ]
    
    for starter in follow_up_starters:
        if question.startswith(starter):
            logger.debug(f"Follow-up starter detected: '{starter}'")
            return True
    
    # Heuristic 3: Time-shift patterns without entity
    time_shift_patterns = [
        r"^(ב)?(חודש|שנה|שבוע|יום)\s+(הבא|שעבר|האחרון)",
        r"^(ב)?(אותו|אותה)\s+(חודש|שנה|שבוע)",
        r"^עכשיו",
        r"^השנה",
        r"^החודש"
    ]
    
    for pattern in time_shift_patterns:
        if re.search(pattern, question):
            # Check if question lacks main entity (no mention of "לקוח", "מכירה", etc.)
            entities = ["לקוח", "מכירה", "הזמנה", "פריט", "מוצר", "עיר", "קבוצה"]
            has_entity = any(entity in question for entity in entities)
            
            if not has_entity:
                logger.debug(f"Time-shift without entity - likely follow-up")
                return True
    
    # Heuristic 4: Questions starting with comparative words
    comparative_starters = ["יותר", "פחות", "גבוה", "נמוך", "גדול", "קטן"]
    if any(question.startswith(comp) for comp in comparative_starters):
        logger.debug("Comparative starter - likely follow-up")
        return True
    
    # Heuristic 5: Questions with only modifiers (no subject)
    modifier_only_patterns = [
        r"^ב[א-ת]+\s*\?*$",  # "בירושלים?", "בשנה?"
        r"^מ[א-ת]+\s*\?*$",  # "מהעיר?", "מהקבוצה?"
    ]
    
    for pattern in modifier_only_patterns:
        if re.match(pattern, question):
            logger.debug("Modifier-only pattern - likely follow-up")
            return True
    
    logger.debug("No follow-up patterns detected")
    return False


def summarize_answer(answer_text: str, max_length: int = 100) -> str:
    """
    Create a very short 1-sentence summary of the answer in Hebrew.
    
    Extracts the first meaningful sentence or truncates to max_length.
    
    Args:
        answer_text: Full answer text in Hebrew
        max_length: Maximum length for summary (default 100 chars)
        
    Returns:
        Short 1-sentence summary in Hebrew
    """
    if not answer_text:
        return ""
    
    # Remove extra whitespace
    answer_text = " ".join(answer_text.split())
    
    # Try to extract first sentence
    sentences = re.split(r'[.!?]\s+', answer_text)
    
    if sentences:
        first_sentence = sentences[0].strip()
        
        # If first sentence is reasonable length, use it
        if len(first_sentence) <= max_length:
            summary = first_sentence
        else:
            # Truncate to max_length at word boundary
            words = first_sentence.split()
            summary = ""
            for word in words:
                if len(summary) + len(word) + 1 <= max_length - 3:
                    summary += (" " if summary else "") + word
                else:
                    break
            summary += "..."
    else:
        # Fallback: truncate to max_length
        summary = answer_text[:max_length - 3] + "..."
    
    logger.debug(f"Created summary ({len(summary)} chars): {summary}")
    return summary


def build_context_block(
    prev_question: str,
    prev_answer_summary: str,
    prev_sql_snippet: Optional[str] = None
) -> str:
    """
    Build a compact context block for the prompt.
    
    Args:
        prev_question: Previous user question
        prev_answer_summary: Short 1-sentence summary of previous answer
        prev_sql_snippet: Optional truncated SQL query
        
    Returns:
        Formatted context block in Hebrew
    """
    context_lines = [
        "הקשר קודם:",
        f'שאלה קודמת: "{prev_question}"',
        f'תשובה קודמת: {prev_answer_summary}'
    ]
    
    if prev_sql_snippet:
        context_lines.append(f'SQL קודם: {prev_sql_snippet}')
    
    return "\n".join(context_lines)
