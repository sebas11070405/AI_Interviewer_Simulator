import { useState } from "react";
import StartScreen from "./pages/StartScreen";
import InterviewScreen from "./pages/InterviewScreen";
import ResultsScreen from "./pages/ResultsScreen";
import "./App.css";

export default function App() {
  const [screen, setScreen] = useState("start");
  const [session, setSession] = useState(null);
  const [summary, setSummary] = useState(null);

  function handleSessionStarted(sessionData) {
    setSession(sessionData);
    setScreen("interview");
  }

  function handleInterviewComplete(summaryData) {
    setSummary(summaryData);
    setScreen("results");
  }

  function handleRestart() {
    setSession(null);
    setSummary(null);
    setScreen("start");
  }

  return (
    <div className="app">
      {screen === "start" && (
        <StartScreen onSessionStarted={handleSessionStarted} />
      )}
      {screen === "interview" && (
        <InterviewScreen
          session={session}
          onComplete={handleInterviewComplete}
        />
      )}
      {screen === "results" && (
        <ResultsScreen summary={summary} onRestart={handleRestart} />
      )}
    </div>
  );
}