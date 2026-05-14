"""
Scoring & Recommendation Module
=================================
Calculates Technical Score, Communication Score,
and generates hiring recommendations.
"""


def calculate_technical_score(test_results=None, interview_results=None):
    """
    Calculate overall technical score (0-100).

    Args:
        test_results: output from evaluator.evaluate_full_test()
        interview_results: output from InterviewSession.end_session()

    Returns:
        int (0-100)
    """
    scores = []

    if test_results:
        scores.append(test_results.get("overall_score", 0))

    if interview_results:
        scores.append(interview_results.get("avg_correctness", 0))

    if not scores:
        return 0

    return round(sum(scores) / len(scores), 1)


def calculate_communication_score(interview_results=None):
    """
    Calculate communication score (0-100).

    Args:
        interview_results: output from InterviewSession.end_session()

    Returns:
        int (0-100)
    """
    if not interview_results:
        return 0

    return round(interview_results.get("avg_communication", 0), 1)


def generate_recommendation(tech_score, comm_score):
    """
    Generate hiring recommendation.

    Args:
        tech_score: 0-100
        comm_score: 0-100

    Returns:
        {
            "decision": "Selected" | "Rejected" | "Needs Improvement",
            "badge": "✅" | "❌" | "⚠️",
            "color": "green" | "red" | "orange",
            "summary": str
        }
    """
    overall = tech_score * 0.65 + comm_score * 0.35

    if overall >= 70:
        return {
            "decision": "Selected",
            "badge": "PASS",
            "color": "#00e676",
            "summary": (
                f"Strong candidate with technical score of {tech_score}/100 "
                f"and communication score of {comm_score}/100. "
                "Recommended for the next round or direct offer."
            )
        }
    elif overall >= 45:
        return {
            "decision": "Needs Improvement",
            "badge": "REVIEW",
            "color": "#ff9100",
            "summary": (
                f"Candidate shows potential (technical: {tech_score}/100, "
                f"communication: {comm_score}/100) but needs to strengthen "
                f"{'technical skills' if tech_score < comm_score else 'communication skills'}. "
                "Consider giving a second chance after preparation."
            )
        }
    else:
        return {
            "decision": "Rejected",
            "badge": "FAIL",
            "color": "#ff1744",
            "summary": (
                f"Candidate scored below expectations (technical: {tech_score}/100, "
                f"communication: {comm_score}/100). Significant preparation needed "
                "in both technical knowledge and interview skills."
            )
        }


def generate_report(profile=None, test_results=None, interview_results=None):
    """
    Generate a comprehensive final report.

    Returns:
        {
            "candidate_profile": {...},
            "technical_score": float,
            "communication_score": float,
            "overall_score": float,
            "recommendation": {...},
            "test_breakdown": {...},
            "interview_breakdown": {...},
            "strengths_identified": [...],
            "improvement_areas": [...],
            "tips": [...]
        }
    """
    tech_score = calculate_technical_score(test_results, interview_results)
    comm_score = calculate_communication_score(interview_results)
    overall = round(tech_score * 0.65 + comm_score * 0.35, 1)
    recommendation = generate_recommendation(tech_score, comm_score)

    # Collect improvement areas
    improvements = []
    if test_results:
        for sr in test_results.get("short_results", []):
            if sr.get("score", 100) < 60:
                improvements.append(f"Short Answer — {sr.get('question', 'N/A')}: {sr.get('improvements', '')}")
        for cr in test_results.get("coding_results", []):
            if cr.get("score", 100) < 60:
                improvements.append(f"Coding — {cr.get('question', 'N/A')}: {cr.get('improvements', '')}")

    if interview_results:
        for entry in interview_results.get("hr_answers", []) + interview_results.get("technical_answers", []):
            eval_data = entry.get("evaluation", {})
            if eval_data.get("overall_score", 100) < 50:
                improvements.append(f"Interview — {entry.get('question', 'N/A')}: {eval_data.get('improvements', '')}")

    # Tips
    tips = []
    if tech_score < 50:
        tips.append("Focus on fundamentals: data structures, algorithms, and core concepts for your role.")
        tips.append("Practice coding problems daily on platforms like LeetCode or HackerRank.")
    if comm_score < 50:
        tips.append("Practice the STAR method for behavioral questions.")
        tips.append("Record yourself answering questions to improve clarity and confidence.")
    if tech_score >= 50 and comm_score >= 50:
        tips.append("Good foundation! Focus on system design and advanced topics.")
        tips.append("Practice mock interviews to build confidence.")
    tips.append("Review your weaknesses identified in the resume analysis.")
    tips.append("Research the company culture and values before real interviews.")

    return {
        "candidate_profile": profile or {},
        "technical_score": tech_score,
        "communication_score": comm_score,
        "overall_score": overall,
        "recommendation": recommendation,
        "test_breakdown": test_results or {},
        "interview_breakdown": interview_results or {},
        "strengths_identified": profile.get("strengths", []) if profile else [],
        "improvement_areas": improvements[:10],
        "tips": tips
    }
