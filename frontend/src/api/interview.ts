const BASE_URL = "http://localhost:8000";

export interface StartSessionResponse {
  session_id: number;
  questions: { id: number; text: string; topic: string | null }[];
}

export interface AnswerResponse {
  score: number;
  explanation: string;
  average_so_far: number;
  complete: boolean;
}

export interface SessionSummary {
  session_id: number;
  total_score: number;
  average_score: number;
  results: {
    question: string;
    answer: string;
    score: number;
    explanation: string;
  }[];
}

export async function startSession(
  topic: string,
  difficulty: string,
  numQuestions: number
): Promise<StartSessionResponse> {
  const res = await fetch(`${BASE_URL}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, difficulty, num_questions: numQuestions }),
  });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function submitAnswer(
  sessionId: number,
  questionIndex: number,
  answer: string
): Promise<AnswerResponse> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question_index: questionIndex, answer }),
  });
  if (!res.ok) throw new Error("Failed to submit answer");
  return res.json();
}

export async function getSessionSummary(sessionId: number): Promise<SessionSummary> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/summary`);
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}