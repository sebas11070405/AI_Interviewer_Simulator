from unittest import result

from questions import generate_questions
from scoring import evaluate_answer

def run_interview():
    questions = generate_questions()

    total_score = 0

    for question in questions:

        print("\nQuestion:")
        print(question)

        answer = input("\nYour answer: ")

        result = evaluate_answer(
            question,
            answer
        )

        print("\nResult:")
        #print(result)
        print(f"\nScore: {result['score']}/10")
        print(f"Feedback: {result['explanation']}")

        total_score += result["score"]

    print("\nInterview Complete")
    print(f"Total Score: {total_score}")