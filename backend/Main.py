import os
import uuid
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from voice_analysis import analyze_voice_delivery
from fastapi import UploadFile, File
import tempfile

#from webcam_analysis import latest_results, results_lock
WEBCAM_RESULTS_FILE = os.path.join(os.path.dirname(__file__), "webcam_results.json")

from database import get_db, engine
from models import Base, Interview, Question, Answer, User
from questions import generate_questions
from scoring import evaluate_answer

load_dotenv()

# Create all tables if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Interview Simulator", version="1.0.0")

# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:5173"],
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
   ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas (request / response shapes)
# ---------------------------------------------------------------------------

class StartSessionResponse(BaseModel):
    session_id: int
    questions: list[dict]


class AnswerRequest(BaseModel):
    session_id: int
    question_index: int
    answer: str


class AnswerResponse(BaseModel):
    score: float
    explanation: str
    average_so_far: float
    complete: bool

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/webcam-status")
def webcam_status():
    if not os.path.exists(WEBCAM_RESULTS_FILE):
        raise HTTPException(status_code=503, detail="Webcam analysis not running")
    try:
        with open(WEBCAM_RESULTS_FILE, "r") as f:
            data = json.load(f)
        if not data.get("ready"):
            raise HTTPException(status_code=503, detail="Waiting for face detection")
        return data
    except Exception:
        raise HTTPException(status_code=503, detail="Webcam analysis not running")

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Accept an audio file from the browser, send it to Whisper,
    return the transcribed text.
    """
    # Save the uploaded audio to a temp file (Whisper's SDK needs a file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from scoring import client  # reuse the same OpenAI client instance
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
        return {"text": transcript.text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Transcription failed: {str(e)}")
    finally:
        os.remove(tmp_path)

@app.post("/analyze-voice")
async def analyze_voice(audio: UploadFile = File(...)):
    """
    Accept an audio recording and return delivery feedback:
    pacing, pauses, pitch/volume variation, and plain-language tips.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
 
    try:
        result = analyze_voice_delivery(tmp_path)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Voice analysis failed: {str(e)}")
    finally:
        os.remove(tmp_path)
 

@app.post("/sessions", response_model=StartSessionResponse)
def start_session(num_questions: int = 3, db: Session = Depends(get_db)):
    """
    Start a new interview session.
    - Creates a guest user if needed
    - Generates questions via OpenAI
    - Saves session + questions to MySQL
    - Returns the session ID and questions to the frontend
    """
    # Create a guest user for now (replace with real auth later)
    user = User(username="guest")
    db.add(user)
    db.flush()  # Get the user_id without committing yet

    # Create the interview session
    interview = Interview(
        user_id=user.user_id,
        interview_date=datetime.utcnow(),
        status="in_progress",
    )
    db.add(interview)
    db.flush()  # Get interview_id

    # Generate questions via OpenAI
    try:
        generated = generate_questions()
    #except Exception as e:
    #    db.rollback()
    #    raise HTTPException(status_code=502, detail=f"Failed to generate questions: {str(e)}")
    except Exception as e:
      db.rollback()
      import traceback
      traceback.print_exc()
      raise HTTPException(status_code=502, detail=f"Failed to generate questions: {str(e)}")

    # Save each question to MySQL
    saved_questions = []
    for q in generated:
        question = Question(
            question_text=q,
            topic=None,
        )
        db.add(question)
        db.flush()
        saved_questions.append({"id": question.question_id, "text": q, "topic": None})

    #interview.questions_json = json.dumps([q.question_id for q in db.query(Question).order_by(Question.question_id.desc()).limit(num_questions).all()][::-1])
    import json
    interview.questions_json = json.dumps([q["id"] for q in saved_questions])

    db.commit()

    return StartSessionResponse(
        session_id=interview.interview_id,
        questions=saved_questions,
    )


@app.post("/sessions/{session_id}/answers", response_model=AnswerResponse)
def submit_answer(session_id: int, body: AnswerRequest, db: Session = Depends(get_db)):
    """
    Submit an answer to one question.
    - Evaluates the answer via OpenAI
    - Saves the answer, score, and feedback to MySQL
    - Returns score + feedback to the frontend
    """
    interview = db.query(Interview).filter(Interview.interview_id == session_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Session not found")

    if interview.status == "completed":
        raise HTTPException(status_code=400, detail="This interview is already complete")

    # Get the question from DB by index
    question_ids = json.loads(interview.questions_json)
    if body.question_index >= len(question_ids):
        raise HTTPException(status_code=400, detail="Invalid question index")
    question = db.query(Question).filter(Question.question_id == question_ids[body.question_index]).first()

    # Evaluate via OpenAI
    try:
        result = evaluate_answer(question.question_text, body.answer)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Failed to evaluate answer: {str(e)}")

    # Save answer to DB
    answer = Answer(
        interview_id=session_id,
        question_id=question.question_id,
        answer_text=body.answer,
        score=result["score"],
        feedback=result["explanation"],
    )
    db.add(answer)

    # Recalculate average
    all_answers = db.query(Answer).filter(Answer.interview_id == session_id).all()
    scores = [float(a.score) for a in all_answers] + [result["score"]]
    average = sum(scores) / len(scores)

    # Check if interview is complete
    total_questions = len(question_ids)
    complete = len(scores) >= total_questions

    if complete:
        interview.status = "completed"
        interview.overall_score = average

    db.commit()

    return AnswerResponse(
        score=result["score"],
        explanation=result["explanation"],
        average_so_far=round(average, 2),
        complete=complete,
    )


@app.get("/sessions/{session_id}/summary")
def get_summary(session_id: int, db: Session = Depends(get_db)):
    """
    Return the full results for a completed session.
    """
    interview = db.query(Interview).filter(Interview.interview_id == session_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Session not found")

    answers = db.query(Answer).filter(Answer.interview_id == session_id).all()

    results = []
    for a in answers:
        question = db.query(Question).filter(Question.question_id == a.question_id).first()
        results.append({
            "question": question.question_text if question else "",
            "answer": a.answer_text,
            "score": float(a.score),
            "explanation": a.feedback,
        })

    scores = [r["score"] for r in results]
    total = sum(scores)
    average = total / len(scores) if scores else 0

    return {
        "session_id": session_id,
        "total_score": round(total, 2),
        "average_score": round(average, 2),
        "results": results,
    }


@app.get("/health")
def health():
    return {"status": "ok"}