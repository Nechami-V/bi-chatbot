import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the AI processor
from app.services.ai_processor import AIQuestionProcessor
from app.db.database import get_db, init_db

def test_ai_processor():
    """Test the AI processor with a sample question."""
    # Initialize database connection
    db = next(get_db())
    
    try:
        # Initialize the AI processor
        print("Initializing AI Processor...")
        ai_processor = AIQuestionProcessor(db)
        
        # Test with a sample question
        question = "Show me all customers"
        print(f"\nProcessing question: {question}")
        
        # Process the question
        result = ai_processor.process_question(question)
        
        # Print the results
        print("\nResults:")
        print(f"Question: {result.get('question')}")
        print(f"Response: {result.get('response')}")
        print(f"SQL: {result.get('sql')}")
        
        if result.get('error'):
            print(f"Error: {result.get('error')}")
        
        print("\nSchema Analysis:")
        print(f"Tables found: {', '.join(ai_processor.schema_info['tables'].keys())}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_processor()
