"""
Voice routes for BI Chatbot API

Contains voice-based query endpoints using speech-to-text transcription.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import tempfile
import openai
from dotenv import load_dotenv

from app.db.database import get_db
from app.services.chatbot_service import ChatbotService
from app.api.auth import verify_token
from app.models.user import User
from app.schemas.chat import QueryRequest, QueryResponse

# Load environment variables
load_dotenv()

router = APIRouter()


def get_openai_key():
    """Get OpenAI API key from environment"""
    return os.getenv('OPENAI_API_KEY', 'api-key')


async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribe audio file using OpenAI Whisper API"""
    
    if audio_file.content_type not in ['audio/webm', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/m4a']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {audio_file.content_type}. Supported formats: webm, wav, mp3, ogg, m4a"
        )
    
    # Read audio content
    audio_content = await audio_file.read()
    
    if len(audio_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty"
        )
    
    # Create temporary file for OpenAI API
    temp_file_path = None
    try:
        # Create temporary file with appropriate extension
        file_extension = '.webm'  # Default
        if audio_file.content_type == 'audio/wav':
            file_extension = '.wav'
        elif audio_file.content_type == 'audio/mp3':
            file_extension = '.mp3'
        elif audio_file.content_type == 'audio/ogg':
            file_extension = '.ogg'
        elif audio_file.content_type == 'audio/m4a':
            file_extension = '.m4a'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        # Check if OpenAI API key is configured
        openai_api_key = get_openai_key()
        if not openai_api_key or openai_api_key == "api-key":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Transcribe audio using Whisper
        with open(temp_file_path, "rb") as audio_data:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                language="he"  # Hebrew
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        transcribed_text = transcript.text.strip()
        
        if not transcribed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transcribe audio. Please ensure the audio contains clear speech."
            )
        
        return transcribed_text
        
    except Exception as e:
        # Clean up temporary file in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        if isinstance(e, HTTPException):
            raise e
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
        )


@router.post("/voice-query", response_model=QueryResponse, tags=["Voice"])
async def voice_query(
    audio_file: UploadFile = File(..., description="Audio file containing voice query"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Process a voice query by transcribing audio and then processing as text

    Accepts audio files in various formats (webm, wav, mp3, ogg, m4a).
    Requires valid JWT token in Authorization header.
    User permissions are checked before processing the question.
    Maximum file size: 25MB
    """
    
    # Step 1: Transcribe the audio file
    transcribed_text = await transcribe_audio(audio_file)
    
    # Step 2: Create a QueryRequest with the transcribed text
    query_request = QueryRequest(question=transcribed_text)
    
    # Step 3: Process the question using existing chatbot service
    # Determine client_id from user or use default
    client_id = getattr(current_user, 'client_id', 'KT')
    if not client_id:
        client_id = 'KT'
    
    chatbot_service = ChatbotService(db, client_id=client_id)
    response = await chatbot_service.process_question(query_request, user=current_user)
    
    # Step 4: Add the transcribed question to the response
    response.question = transcribed_text
    
    return response