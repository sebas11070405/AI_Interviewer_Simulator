import "./ResultsScreen.css";

export default function ResultsScreen({ summary, onRestart }) {
  const { average_score, total_score, results } = summary;

  function getGrade(avg)
  {
    if (avg >= 8) return { label: "Excellent", cls: "grade-a" };
    if (avg >= 6) return { label: "Good", cls: "grade-b" };
    if (avg >= 4) return { label: "Needs Work", cls: "grade-c" };
    return { label: "Keep Practicing", cls: "grade-d" };
  }

  function getScoreClass(score) {
    if (score >= 7) return "score-high";
    if (score >= 4) return "score-mid";
    return "score-low";
  }

  const grade = getGrade(average_score);

  return (
    <div className="results-screen">
      <div className="results-header">
        <h1 className="results-title">Interview Complete</h1>
        <div className={`grade-badge ${grade.cls}`}>{grade.label}</div>
      </div>

      <div className="results-summary">
        <div className="summary-stat">
          <span className="stat-value">{average_score.toFixed(1)}</span>
          <span className="stat-label">Average score</span>
        </div>
        <div className="summary-divider" />
        <div className="summary-stat">
          <span className="stat-value">{total_score.toFixed(1)}</span>
          <span className="stat-label">Total points</span>
        </div>
        <div className="summary-divider" />
        <div className="summary-stat">
          <span className="stat-value">{results.length}</span>
          <span className="stat-label">Questions</span>
        </div>
      </div>

      <div className="results-list">
        {results.map((result, i) => (
          <div className="result-item" key={i}>
            <div className="result-header">
              <span className="result-q">Q{i + 1}</span>
              <span className={`result-score ${getScoreClass(result.score)}`}>
                {result.score}/10
              </span>
            </div>
            <p className="result-question">{result.question}</p>
            <div className="result-divider" />
            <p className="result-answer">
              <span className="result-answer-label">Your answer: </span>
              {result.answer}
            </p>
            <p className="result-feedback">{result.explanation}</p>
          </div>
        ))}
      </div>

      <button className="restart-btn" onClick={onRestart}>
        Start New Interview
      </button>
    </div>
  );
}