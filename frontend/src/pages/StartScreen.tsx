import { useState } from "react";
import { startSession, StartSessionResponse } from "../api/interview";
import "./StartScreen.css";

interface StartScreenProps {
  onSessionStarted: (session: StartSessionResponse) => void;
}

export default function StartScreen({ onSessionStarted }: StartScreenProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      const session = await startSession(3);
      onSessionStarted(session);
    } catch (err) {
      setError("Could not connect to the server. Is FastAPI running?");
      setLoading(false);
    }
  }

  return (
    <div className="start-screen">
      <div className="start-card">
        <div className="start-badge">Software Engineering</div>
        <h1 className="start-title">Interview<br />Simulator</h1>
        <p className="start-description">
          3 technical questions. Instant AI feedback.<br />
          See how you really perform under pressure.
        </p>

        <div className="start-info">
          <div className="info-item">
            <span className="info-number">3</span>
            <span className="info-label">Questions</span>
          </div>
          <div className="info-divider" />
          <div className="info-item">
            <span className="info-number">AI</span>
            <span className="info-label">Scoring</span>
          </div>
          <div className="info-divider" />
          <div className="info-item">
            <span className="info-number">10</span>
            <span className="info-label">Points each</span>
          </div>
        </div>

        {error && <p className="start-error">{error}</p>}

        <button
          className={`start-btn ${loading ? "loading" : ""}`}
          onClick={handleStart}
          disabled={loading}
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