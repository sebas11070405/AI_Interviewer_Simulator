import { useState, useRef, useEffect, useCallback } from "react";
import { submitAnswer, getSessionSummary } from "../api/interview";
import "./InterviewScreen.css";

const TIME_LIMIT_SECONDS = 90;

interface Question {
  text: string;
  topic?: string | null;
}

interface Session {
  session_id: number;
  questions: Question[];
}

interface VoiceFeedback {
  summary: string;
  tips: string[];
  speech_rate_label: string;
  pause_count: number;
}

interface WebcamStatus {
  stress_label: string;
  smile: number;
  looking_away: boolean;
  ear: number;
}

interface InterviewScreenProps {
  session: Session;
  onComplete: (summary: any) => void;
}

export default function InterviewScreen({ session, onComplete }: InterviewScreenProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [voiceFeedback, setVoiceFeedback] = useState<VoiceFeedback | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Timer state
  const [secondsLeft, setSecondsLeft] = useState(TIME_LIMIT_SECONDS);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeUpHandledRef = useRef(false);

  // Webcam state
  const [webcamStatus, setWebcamStatus] = useState<WebcamStatus | null>(null);

  const questions = session.questions;
  const total = questions.length;
  const current = questions[currentIndex];
  const progress = (currentIndex / total) * 100;
  const isLast = currentIndex === total - 1;

  // --- Submit logic ---
  const doSubmit = useCallback(async (answerText: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await submitAnswer(session.session_id, currentIndex, answerText);
      setFeedback(result);
    } catch (err) {
      setError("Failed to evaluate answer. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [session.session_id, currentIndex]);

  async function handleSubmit() {
    if (!answer.trim()) return;
    await doSubmit(answer);
  }

  // --- Timer ---
  const handleTimeUp = useCallback(() => {
    if (timeUpHandledRef.current) return;
    timeUpHandledRef.current = true;
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      doSubmit(answer);
    }
  }, [isRecording, answer, doSubmit]);

  useEffect(() => {
    if (feedback) return;
    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current!);
          handleTimeUp();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [feedback, handleTimeUp]);

  useEffect(() => {
    setSecondsLeft(TIME_LIMIT_SECONDS);
    timeUpHandledRef.current = false;
  }, [currentIndex]);

  useEffect(() => {
    if (secondsLeft === 0 && !isRecording && !isTranscribing && timeUpHandledRef.current && !feedback && !loading) {
      doSubmit(answer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isTranscribing]);

  // --- Webcam status polling ---
  useEffect(() => {
    if (feedback) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("http://localhost:8000/webcam-status");
        if (res.ok) setWebcamStatus(await res.json());
      } catch {
        // Webcam script not running — fail silently
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [feedback]);

  // --- Next question ---
  async function handleNext() {
    if (isLast) {
      setLoading(true);
      try {
        const summary = await getSessionSummary(session.session_id);
        onComplete(summary);
      } catch (err) {
        setError("Failed to load summary.");
        setLoading(false);
      }
    } else {
      setCurrentIndex(currentIndex + 1);
      setAnswer("");
      setFeedback(null);
      setVoiceFeedback(null);
      setWebcamStatus(null);
    }
  }

  function getScoreClass(score: number) {
    if (score >= 7) return "score-high";
    if (score >= 4) return "score-mid";
    return "score-low";
  }

  function formatTime(s: number) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  }

  function getWebcamClass(label: string) {
    if (label === "Confident") return "score-high";
    if (label === "Tense") return "score-low";
    return "score-mid";
  }

  // --- Voice recording ---
  async function startRecording() {
    setError(null);
    setAnswer("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((track) => track.stop());
        await Promise.all([
          sendAudioForTranscription(blob),
          sendAudioForVoiceAnalysis(blob),
        ]);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied or unavailable.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  async function sendAudioForTranscription(blob: Blob) {
    setIsTranscribing(true);
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");
    try {
      const res = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Transcription request failed");
      const data = await res.json();
      setAnswer(data.text);
    } catch (err) {
      setError("Transcription failed. Please try again.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function sendAudioForVoiceAnalysis(blob: Blob) {
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");
    try {
      const res = await fetch("http://localhost:8000/analyze-voice", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) return;
      const data = await res.json();
      setVoiceFeedback(data);
    } catch {
      // Non-critical — fail silently
    }
  }

  return (
    <div className="interview-screen">
      <header className="interview-header">
        <span className="header-label">Interview in progress</span>
        <span className="header-progress">
          Question {currentIndex + 1} of {total}
        </span>
      </header>

      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="interview-body">
        <div className="question-card">
          <div className="question-card-top">
            <div className="question-number">Q{currentIndex + 1}</div>
            {!feedback && (
              <div className={`timer ${secondsLeft <= 15 ? "timer-low" : ""}`}>
                {formatTime(secondsLeft)}
              </div>
            )}
          </div>
          <p className="question-text">{current.text}</p>
          {current.topic && (
            <span className="question-topic">{current.topic}</span>
          )}
        </div>

        {!feedback ? (
          <div className="answer-section">

            {webcamStatus && (
              <div className="webcam-status">
                <span className="webcam-label">Confidence</span>
                <span className={`webcam-indicator ${getWebcamClass(webcamStatus.stress_label)}`}>
                  {webcamStatus.stress_label}
                </span>
                {webcamStatus.looking_away && (
                  <span className="webcam-warning">⚠ Look at the camera</span>
                )}
              </div>
            )}

            <div className="answer-label-row">
              <label className="answer-label">Your answer (voice only)</label>
              <button
                type="button"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isTranscribing || loading}
                className={`mic-btn ${isRecording ? "recording" : ""}`}
              >
                {isTranscribing ? (
                  <><span className="spinner" /> Transcribing…</>
                ) : isRecording ? (
                  <>⏹ Stop Recording</>
                ) : answer ? (
                  <>🎤 Re-record Answer</>
                ) : (
                  <>🎤 Record Answer</>
                )}
              </button>
            </div>

            <textarea
              className="answer-input"
              value={answer}
              readOnly
              placeholder={`Press "Record Answer" and speak — your words will appear here.`}
              rows={6}
            />

            {answer && !isRecording && !isTranscribing && (
              <p className="rerecord-hint">
                Not happy with this? Click "Re-record Answer" above to try again.
              </p>
            )}

            {error && <p className="error-msg">{error}</p>}

            {voiceFeedback && (
              <div className="voice-feedback">
                <span className="voice-feedback-label">Delivery</span>
                <p className="voice-feedback-summary">{voiceFeedback.summary}</p>
                {voiceFeedback.tips.length > 0 && (
                  <ul className="voice-feedback-tips">
                    {voiceFeedback.tips.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <button
              className={`submit-btn ${loading ? "loading" : ""}`}
              onClick={handleSubmit}
              disabled={loading || isTranscribing || !answer.trim()}
            >
              {loading ? (
                <><span className="spinner" /> Evaluating…</>
              ) : (
                "Submit Answer"
              )}
            </button>
          </div>
        ) : (
          <div className="feedback-card">
            <div className="feedback-top">
              <span className="feedback-label">Score</span>
              <span className={`feedback-score ${getScoreClass(feedback.score)}`}>
                {feedback.score}
                <span className="score-denom">/10</span>
              </span>
            </div>
            <div className="score-track">
              <div
                className={`score-fill ${getScoreClass(feedback.score)}`}
                style={{ width: `${feedback.score * 10}%` }}
              />
            </div>
            <p className="feedback-text">{feedback.explanation}</p>
            <button className="next-btn" onClick={handleNext} disabled={loading}>
              {loading ? (
                <><span className="spinner" /> Loading…</>
              ) : isLast ? (
                "View Results →"
              ) : (
                "Next Question →"
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}