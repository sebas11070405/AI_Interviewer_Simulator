import { useState } from "react";
import { startSession, StartSessionResponse } from "../api/interview";
import "./StartScreen.css";

interface StartScreenProps {
  onSessionStarted: (session: StartSessionResponse) => void;
}

const DIFFICULTIES = ["Easy", "Medium", "Hard"];
const QUESTION_COUNTS = [3, 5, 10];

export default function StartScreen({ onSessionStarted }: StartScreenProps) {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("Medium");
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    if (!topic.trim()) {
      setError("Please enter a topic.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const session = await startSession(topic.trim(), difficulty, numQuestions);
      onSessionStarted(session);
    } catch (err) {
      setError("Could not connect to the server. Is FastAPI running?");
      setLoading(false);
    }
  }

  return (
    <div className="start-screen">
      <div className="start-card">
        <div className="start-badge">AI Interview Simulator</div>
        <h1 className="start-title">Interview<br />Simulator</h1>
        <p className="start-description">
          Enter any topic, choose a difficulty, and get instant AI feedback.
        </p>

        <div className="start-form">
          <div className="form-group">
            <label className="form-label">Topic</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. Python, Machine Learning, System Design…"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStart()}
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Difficulty</label>
              <div className="btn-group">
                {DIFFICULTIES.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={`btn-option ${difficulty === d ? "active" : ""}`}
                    onClick={() => setDifficulty(d)}
                    disabled={loading}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Questions</label>
              <div className="btn-group">
                {QUESTION_COUNTS.map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={`btn-option ${numQuestions === n ? "active" : ""}`}
                    onClick={() => setNumQuestions(n)}
                    disabled={loading}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {error && <p className="start-error">{error}</p>}

        <button
          className={`start-btn ${loading ? "loading" : ""}`}
          onClick={handleStart}
          disabled={loading || !topic.trim()}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Generating questions…
            </>
          ) : (
            "Begin Interview"
          )}
        </button>
      </div>
    </div>
  );
}