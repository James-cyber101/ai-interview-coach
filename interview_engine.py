"""
Interview Engine Module
========================
Manages AI interview sessions with dynamic question generation,
follow-up logic, and HR + Technical round simulation.
"""

import random
import re

# ---------------------------------------------------------------------------
# Question banks for interview rounds
# ---------------------------------------------------------------------------

HR_QUESTIONS = [
    "Tell me about yourself.",
    "Why do you want to work at our company?",
    "What are your greatest strengths?",
    "What is your biggest weakness and how are you working on it?",
    "Where do you see yourself in 5 years?",
    "Describe a challenging situation you faced and how you handled it.",
    "Why should we hire you over other candidates?",
    "Tell me about a time you worked in a team.",
    "How do you handle pressure and tight deadlines?",
    "What motivates you in your career?",
    "Describe a conflict you had with a colleague and how you resolved it.",
    "What are your salary expectations?",
    "Do you prefer working independently or in a team?",
    "How do you prioritize your tasks?",
    "What do you know about our company?"
]

TECHNICAL_QUESTIONS_BY_ROLE = {
    "Data Analyst": [
        "Explain the difference between INNER JOIN and LEFT JOIN with examples.",
        "How would you handle missing data in a dataset?",
        "What is the difference between a data warehouse and a data lake?",
        "Explain what an ETL pipeline is and its stages.",
        "How do you create a pivot table in Python/Pandas?",
        "What metrics would you use to evaluate a marketing campaign?",
        "Explain the concept of data normalization.",
        "How would you detect outliers in a dataset?",
        "What is the difference between correlation and causation?",
        "Walk me through how you would build a dashboard for sales data."
    ],
    "Data Scientist": [
        "Explain the bias-variance tradeoff.",
        "What is cross-validation and why is it important?",
        "How does a Random Forest algorithm work?",
        "Explain the difference between L1 and L2 regularization.",
        "How would you handle imbalanced classes in a classification problem?",
        "What is feature engineering? Give examples.",
        "Explain gradient descent and its variants.",
        "How do you evaluate a regression model?",
        "What is the curse of dimensionality?",
        "Explain how a neural network learns through backpropagation."
    ],
    "Software Engineer": [
        "Explain the difference between a stack and a queue.",
        "What is time complexity and how do you analyze it?",
        "Explain object-oriented programming principles.",
        "What is the difference between a process and a thread?",
        "How does garbage collection work in Python/Java?",
        "Explain REST API design principles.",
        "What design patterns have you used in your projects?",
        "Explain the concept of database indexing.",
        "What is the difference between SQL and NoSQL databases?",
        "How would you design a URL shortener system?"
    ],
    "AI Engineer": [
        "What is the difference between supervised and unsupervised learning?",
        "Explain how convolutional neural networks work.",
        "What is transfer learning and when would you use it?",
        "How do you handle overfitting in deep learning models?",
        "Explain the attention mechanism in transformers.",
        "What is the difference between GAN and VAE?",
        "How would you deploy an ML model to production?",
        "Explain batch normalization and why it helps.",
        "What is the role of the learning rate in training?",
        "How do you evaluate a classification model beyond accuracy?"
    ],
    "Backend Engineer": [
        "Explain the concept of microservices architecture.",
        "What is database sharding and when would you use it?",
        "How do you handle authentication in a REST API?",
        "Explain the CAP theorem.",
        "What is message queuing and when would you use it?",
        "How do you optimize a slow SQL query?",
        "Explain horizontal vs vertical scaling.",
        "What is rate limiting and how would you implement it?",
        "How do you design for high availability?",
        "Explain caching strategies — when to use Redis vs Memcached?"
    ],
    "Frontend Engineer": [
        "Explain the Virtual DOM and how React uses it.",
        "What is the difference between SSR and CSR?",
        "How do you optimize web performance?",
        "Explain CSS specificity and the cascade.",
        "What are React hooks and why were they introduced?",
        "How do you handle state management in large React apps?",
        "Explain the event loop in JavaScript.",
        "What is a closure in JavaScript?",
        "How do you make a website accessible?",
        "Explain lazy loading and code splitting."
    ],
    "ML Engineer": [
        "How do you monitor ML models in production?",
        "Explain feature stores and their importance.",
        "What is ML pipeline orchestration?",
        "How do you handle data drift?",
        "Explain A/B testing for ML models.",
        "What is model versioning and why is it important?",
        "How would you scale model training?",
        "Explain the difference between batch and online learning.",
        "What is MLOps and why is it important?",
        "How do you ensure reproducibility in ML experiments?"
    ],
    "Full Stack Developer": [
        "How would you design the architecture for a full-stack app?",
        "Explain the request lifecycle in a web application.",
        "What is CORS and how do you handle it?",
        "How do you manage environment-specific configurations?",
        "Explain database migrations and their importance.",
        "What is WebSocket and when would you use it over REST?",
        "How do you handle file uploads in a web application?",
        "Explain JWT authentication flow.",
        "What is server-side rendering and its benefits?",
        "How do you implement real-time features in a web app?"
    ],
    "DevOps Engineer": [
        "Explain the CI/CD pipeline and its stages.",
        "What is infrastructure as code?",
        "How does Docker containerization work?",
        "Explain Kubernetes pod lifecycle.",
        "What is blue-green deployment?",
        "How do you monitor application health in production?",
        "Explain the difference between Terraform and Ansible.",
        "What is service mesh?",
        "How do you handle secrets management?",
        "Explain the concept of immutable infrastructure."
    ],
    "Cybersecurity Engineer": [
        "Explain the OWASP Top 10 vulnerabilities.",
        "How does TLS/SSL encryption work?",
        "What is the zero trust security model?",
        "Explain SQL injection and how to prevent it.",
        "What is cross-site scripting (XSS)?",
        "How do you perform a security audit?",
        "Explain the concept of defense in depth.",
        "What is penetration testing?",
        "How do you handle incident response?",
        "Explain the difference between symmetric and asymmetric encryption."
    ]
}

# Follow-up question templates
FOLLOWUP_TEMPLATES = {
    "shallow": [
        "Can you go deeper into that? What are the specific steps?",
        "Can you give a concrete example from your experience?",
        "How would you implement that in practice?",
        "What tools or technologies would you use for that?",
        "What would happen if that approach fails? What's your Plan B?"
    ],
    "moderate": [
        "That's a good start. Can you explain the trade-offs involved?",
        "How does this compare to alternative approaches?",
        "What challenges might you face implementing this?",
        "How would you test or validate that solution?",
        "Can you relate this to a real-world scenario?"
    ],
    "strong": [
        "Good answer. How would you optimize this at scale?",
        "What edge cases should be considered?",
        "How would this work in a distributed system?",
        "What metrics would you use to measure success?",
        "Excellent. Let's move to the next topic."
    ]
}

PROJECT_QUESTION_TEMPLATES = [
    "Tell me more about your project: '{project}'. What was your role?",
    "What was the biggest challenge you faced in '{project}'?",
    "What technologies did you use in '{project}' and why?",
    "How did you test and deploy '{project}'?",
    "If you could redo '{project}', what would you do differently?",
    "What did you learn from working on '{project}'?"
]


# ---------------------------------------------------------------------------
# Interview Session class
# ---------------------------------------------------------------------------

class InterviewSession:
    """
    Manages a complete interview session with HR and Technical rounds.

    Usage:
        session = InterviewSession(role="Data Scientist", profile={...})
        q = session.get_next_question()
        evaluation = session.submit_answer(answer_text)
        q2 = session.get_next_question()  # may be follow-up
        ...
        report = session.end_session()
    """

    def __init__(self, role="Software Engineer", profile=None):
        self.role = role
        self.profile = profile or {}
        self.current_round = "hr"  # "hr" or "technical"
        self.question_index = 0
        self.history = []  # list of { question, answer, evaluation, round }
        self.current_question = None
        self.follow_up_pending = False

        # Prepare question pools
        self._hr_questions = random.sample(HR_QUESTIONS, min(5, len(HR_QUESTIONS)))
        # Always start HR with "Tell me about yourself"
        if "Tell me about yourself." not in self._hr_questions:
            self._hr_questions.insert(0, "Tell me about yourself.")
        else:
            self._hr_questions.remove("Tell me about yourself.")
            self._hr_questions.insert(0, "Tell me about yourself.")

        # Technical questions
        tech_pool = TECHNICAL_QUESTIONS_BY_ROLE.get(role, [])
        if not tech_pool:
            # Fallback: use Software Engineer
            tech_pool = TECHNICAL_QUESTIONS_BY_ROLE["Software Engineer"]
        self._tech_questions = random.sample(tech_pool, min(5, len(tech_pool)))

        # Add project-based questions from resume
        projects = self.profile.get("projects", [])
        self._project_questions = []
        for proj in projects[:2]:  # Max 2 project deep-dives
            template = random.choice(PROJECT_QUESTION_TEMPLATES)
            self._project_questions.append(template.format(project=proj))

        self._tech_questions = self._project_questions + self._tech_questions
        self._tech_questions = self._tech_questions[:7]  # Cap total

        self.total_hr = len(self._hr_questions)
        self.total_tech = len(self._tech_questions)

    def get_status(self):
        """Return current session status."""
        return {
            "current_round": self.current_round,
            "questions_answered": len(self.history),
            "total_hr_questions": self.total_hr,
            "total_tech_questions": self.total_tech,
            "is_complete": self._is_complete()
        }

    def _is_complete(self):
        hr_done = self.question_index >= self.total_hr if self.current_round == "hr" else True
        tech_done = self.question_index >= self.total_tech if self.current_round == "technical" else False
        if self.current_round == "technical" and self.question_index >= self.total_tech:
            tech_done = True
        return hr_done and tech_done if self.current_round == "technical" else False

    def get_next_question(self):
        """
        Get the next interview question.
        Returns dict: { "question": str, "round": str, "number": int, "total": int }
        or None if interview is complete.
        """
        if self.follow_up_pending:
            self.follow_up_pending = False
            return {
                "question": self.current_question,
                "round": self.current_round,
                "number": self.question_index,
                "total": self.total_hr if self.current_round == "hr" else self.total_tech,
                "is_followup": True
            }

        if self.current_round == "hr":
            if self.question_index < self.total_hr:
                q = self._hr_questions[self.question_index]
                self.current_question = q
                return {
                    "question": q,
                    "round": "HR Round",
                    "number": self.question_index + 1,
                    "total": self.total_hr,
                    "is_followup": False
                }
            else:
                # Switch to technical round
                self.current_round = "technical"
                self.question_index = 0
                return self.get_next_question()

        if self.current_round == "technical":
            if self.question_index < self.total_tech:
                q = self._tech_questions[self.question_index]
                self.current_question = q
                return {
                    "question": q,
                    "round": "Technical Round",
                    "number": self.question_index + 1,
                    "total": self.total_tech,
                    "is_followup": False
                }

        return None  # Interview complete

    def submit_answer(self, answer_text):
        """
        Submit an answer to the current question. Returns evaluation + possible follow-up.

        Returns:
            {
                "evaluation": { ... },
                "has_followup": bool
            }
        """
        from evaluator import evaluate_interview_answer

        evaluation = evaluate_interview_answer(
            self.current_question, answer_text, self.profile
        )

        self.history.append({
            "question": self.current_question,
            "answer": answer_text,
            "evaluation": evaluation,
            "round": self.current_round
        })

        # Decide follow-up
        score = evaluation["overall_score"]
        has_followup = False

        if score < 40:
            # Weak answer — ask a follow-up to give another chance
            followup = random.choice(FOLLOWUP_TEMPLATES["shallow"])
            self.current_question = followup
            self.follow_up_pending = True
            has_followup = True
        elif score < 70:
            # Moderate — sometimes probe deeper
            if random.random() < 0.5:
                followup = random.choice(FOLLOWUP_TEMPLATES["moderate"])
                self.current_question = followup
                self.follow_up_pending = True
                has_followup = True
            else:
                self.question_index += 1
        else:
            # Strong answer — acknowledge and move on
            if random.random() < 0.2:
                followup = random.choice(FOLLOWUP_TEMPLATES["strong"])
                self.current_question = followup
                self.follow_up_pending = True
                has_followup = True
            else:
                self.question_index += 1

        if not has_followup:
            # Check if we need to advance
            pass  # question_index already incremented

        return {
            "evaluation": evaluation,
            "has_followup": has_followup
        }

    def end_session(self):
        """
        End the interview and return a full summary.

        Returns:
            {
                "total_questions": int,
                "hr_answers": [...],
                "technical_answers": [...],
                "avg_correctness": float,
                "avg_communication": float,
                "avg_overall": float
            }
        """
        hr_answers = [h for h in self.history if h["round"] == "hr"]
        tech_answers = [h for h in self.history if h["round"] == "technical"]

        all_evals = [h["evaluation"] for h in self.history]

        def avg(key):
            vals = [e.get(key, 0) for e in all_evals]
            return round(sum(vals) / len(vals), 1) if vals else 0

        return {
            "total_questions": len(self.history),
            "hr_answers": hr_answers,
            "technical_answers": tech_answers,
            "avg_correctness": avg("correctness_score"),
            "avg_communication": avg("communication_score"),
            "avg_overall": avg("overall_score")
        }
