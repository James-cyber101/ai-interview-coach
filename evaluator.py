"""
Answer Evaluator Module
========================
Evaluates MCQ, short-answer, and coding responses.
Provides scores, feedback, and improvement suggestions.
"""

import re
import math
from collections import Counter

# ---------------------------------------------------------------------------
# Text similarity helpers (no heavy ML dependency)
# ---------------------------------------------------------------------------

def _tokenize(text):
    """Simple word-level tokenizer."""
    return re.findall(r"[a-z0-9]+", text.lower())

def _cosine_similarity(text_a, text_b):
    """Compute cosine similarity between two texts using word frequency vectors."""
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    counter_a = Counter(tokens_a)
    counter_b = Counter(tokens_b)
    all_words = set(counter_a.keys()) | set(counter_b.keys())

    dot = sum(counter_a.get(w, 0) * counter_b.get(w, 0) for w in all_words)
    mag_a = math.sqrt(sum(v ** 2 for v in counter_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in counter_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _keyword_match_score(answer, expected_keywords):
    """Score based on how many expected keywords appear in the answer."""
    if not expected_keywords:
        return 0.5  # neutral
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return hits / len(expected_keywords)


# ---------------------------------------------------------------------------
# Communication quality helpers
# ---------------------------------------------------------------------------

def _assess_communication(answer):
    """
    Rate communication quality 0-100 based on:
    - Length (too short = low, reasonable = high)
    - Sentence structure
    - Vocabulary diversity
    """
    words = _tokenize(answer)
    word_count = len(words)

    if word_count == 0:
        return 0, "No answer provided."

    # Length score
    if word_count < 5:
        length_score = 20
        length_note = "Answer is too short — elaborate more."
    elif word_count < 15:
        length_score = 50
        length_note = "Answer could be more detailed."
    elif word_count < 80:
        length_score = 90
        length_note = "Good level of detail."
    else:
        length_score = 75
        length_note = "Answer is very long — consider being more concise."

    # Vocabulary diversity
    unique_ratio = len(set(words)) / word_count if word_count else 0
    vocab_score = min(100, int(unique_ratio * 130))

    # Sentence count
    sentences = re.split(r"[.!?]+", answer)
    sentences = [s.strip() for s in sentences if s.strip()]
    structure_score = min(100, len(sentences) * 20)

    total = int(length_score * 0.4 + vocab_score * 0.3 + structure_score * 0.3)
    feedback = length_note
    return min(100, total), feedback


# ---------------------------------------------------------------------------
# MCQ Evaluator
# ---------------------------------------------------------------------------

def evaluate_mcq(questions, user_answers):
    """
    Evaluate multiple-choice questions.

    Args:
        questions: list of question dicts from questions.json
        user_answers: dict like { "q1": "Python", "q2": "MySQL", ... }

    Returns:
        {
            "score": int,
            "total": int,
            "percentage": float,
            "details": [ { "question", "user_answer", "correct_answer", "is_correct" } ]
        }
    """
    score = 0
    total = 0
    details = []

    for i, q in enumerate(questions, start=1):
        if q.get("type") != "mcq":
            continue
        total += 1
        correct = q.get("answer", "")
        user_ans = user_answers.get(f"q{i}", "")
        is_correct = (user_ans == correct)
        if is_correct:
            score += 1
        details.append({
            "question": q["question"],
            "user_answer": user_ans or "(no answer)",
            "correct_answer": correct,
            "is_correct": is_correct
        })

    return {
        "score": score,
        "total": total,
        "percentage": round((score / total * 100) if total else 0, 1),
        "details": details
    }


# ---------------------------------------------------------------------------
# Short Answer Evaluator
# ---------------------------------------------------------------------------

def evaluate_short_answer(question, answer, expected_keywords=None):
    """
    Evaluate a short text answer using keyword matching + length heuristics.

    Returns:
        { "score": 0-100, "feedback": str, "improvements": str }
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "feedback": "No answer provided.",
            "improvements": "Provide a clear, concise explanation."
        }

    # Keyword match
    kw_score = _keyword_match_score(answer, expected_keywords or []) * 60

    # Communication
    comm_score, comm_feedback = _assess_communication(answer)
    comm_component = comm_score * 0.4

    total = int(kw_score + comm_component)
    total = min(100, max(0, total))

    # Feedback
    if total >= 80:
        feedback = "Excellent answer with good coverage of key concepts."
        improvements = "Keep it up — consider adding real-world examples."
    elif total >= 50:
        feedback = "Decent answer but missing some key points."
        improvements = "Include more technical details and specific terminology."
    else:
        feedback = "Answer needs significant improvement."
        improvements = "Study the topic thoroughly. Cover definition, working mechanism, and use cases."

    return {
        "score": total,
        "feedback": feedback,
        "improvements": improvements,
        "communication_note": comm_feedback
    }


# ---------------------------------------------------------------------------
# Coding Answer Evaluator
# ---------------------------------------------------------------------------

def evaluate_coding(question, code):
    """
    Evaluate a coding answer using syntax heuristics + keyword detection.
    (Full code execution is not performed for safety.)

    Returns:
        { "score": 0-100, "feedback": str, "improvements": str }
    """
    if not code or not code.strip():
        return {
            "score": 0,
            "feedback": "No code provided.",
            "improvements": "Write a working solution with proper syntax."
        }

    score = 0
    notes = []

    # 1) Length check
    lines = [l for l in code.strip().split("\n") if l.strip()]
    if len(lines) >= 3:
        score += 20
        notes.append("Code has reasonable length.")
    elif len(lines) >= 1:
        score += 10
        notes.append("Code is very short — may be incomplete.")

    # 2) Python syntax markers
    syntax_markers = ["def ", "import ", "class ", "for ", "while ", "if ",
                      "return ", "print(", "=", ":", "range(", "len(",
                      "try:", "except", "with "]
    marker_hits = sum(1 for m in syntax_markers if m in code)
    syntax_score = min(30, marker_hits * 5)
    score += syntax_score

    # 3) Relevance to question
    relevance = _cosine_similarity(question, code)
    relevance_score = int(relevance * 30)
    score += relevance_score

    # 4) Code quality markers
    quality_markers = ["#", '"""', "'''", "def ", "return "]
    quality_hits = sum(1 for m in quality_markers if m in code)
    score += min(20, quality_hits * 5)

    score = min(100, score)

    if score >= 75:
        feedback = "Good code with proper structure and relevant logic."
        improvements = "Consider adding error handling and edge cases."
    elif score >= 40:
        feedback = "Code shows some understanding but needs improvement."
        improvements = "Ensure the code is complete, handles edge cases, and follows best practices."
    else:
        feedback = "Code needs significant work."
        improvements = "Review the fundamentals. Write complete, runnable code with proper structure."

    return {
        "score": score,
        "feedback": feedback,
        "improvements": improvements
    }


# ---------------------------------------------------------------------------
# Interview Answer Evaluator
# ---------------------------------------------------------------------------

def evaluate_interview_answer(question, answer, context=None):
    """
    Evaluate an interview-style answer.

    Args:
        question: the interview question text
        answer: candidate's response
        context: optional dict with resume profile for deeper evaluation

    Returns:
        {
            "correctness_score": 0-100,
            "communication_score": 0-100,
            "overall_score": 0-100,
            "feedback": str,
            "improvements": str
        }
    """
    if not answer or not answer.strip():
        return {
            "correctness_score": 0,
            "communication_score": 0,
            "overall_score": 0,
            "feedback": "No answer provided.",
            "improvements": "Always provide a response, even if unsure."
        }

    # Correctness via relevance
    relevance = _cosine_similarity(question, answer)
    correctness = int(min(100, relevance * 150 + 20))

    # Communication
    comm_score, comm_note = _assess_communication(answer)

    # Bonus for structured answers (STAR method hints)
    star_keywords = ["situation", "task", "action", "result",
                     "example", "for instance", "specifically"]
    star_bonus = sum(3 for kw in star_keywords if kw in answer.lower())
    correctness = min(100, correctness + star_bonus)

    overall = int(correctness * 0.6 + comm_score * 0.4)

    if overall >= 75:
        feedback = "Strong answer demonstrating clear understanding and good communication."
        improvements = "Try to include more specific examples from your experience."
    elif overall >= 45:
        feedback = "Reasonable answer but could be stronger."
        improvements = "Use the STAR method (Situation, Task, Action, Result) for structured responses."
    else:
        feedback = "Answer needs improvement in both content and delivery."
        improvements = "Research the topic, prepare structured answers, and practice articulating clearly."

    return {
        "correctness_score": correctness,
        "communication_score": comm_score,
        "overall_score": overall,
        "feedback": feedback,
        "improvements": improvements,
        "communication_note": comm_note
    }


# ---------------------------------------------------------------------------
# Batch evaluator for a full test
# ---------------------------------------------------------------------------

def evaluate_full_test(questions, user_answers):
    """
    Evaluate all questions in a test (MCQ + short + coding).

    Returns:
        {
            "mcq_result": {...},
            "short_results": [...],
            "coding_results": [...],
            "overall_score": float,
            "total_questions": int
        }
    """
    mcq_questions = [q for q in questions if q.get("type") == "mcq"]
    mcq_result = evaluate_mcq(questions, user_answers)

    short_results = []
    coding_results = []

    for i, q in enumerate(questions, start=1):
        ans = user_answers.get(f"q{i}", "")
        if q["type"] == "short":
            result = evaluate_short_answer(
                q["question"], ans,
                q.get("expected_keywords", [])
            )
            result["question"] = q["question"]
            result["user_answer"] = ans
            short_results.append(result)
        elif q["type"] == "coding":
            result = evaluate_coding(q["question"], ans)
            result["question"] = q["question"]
            result["user_answer"] = ans
            coding_results.append(result)

    # Overall score
    scores = []
    if mcq_result["total"]:
        scores.append(mcq_result["percentage"])
    for r in short_results:
        scores.append(r["score"])
    for r in coding_results:
        scores.append(r["score"])

    overall = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "mcq_result": mcq_result,
        "short_results": short_results,
        "coding_results": coding_results,
        "overall_score": overall,
        "total_questions": len(questions)
    }
