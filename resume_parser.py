"""
Resume Parser Module
====================
Extracts candidate profile data from PDF or plain text resumes.
Identifies skills, education, projects, experience, strengths and weaknesses.
"""

import re
import os

# ---------------------------------------------------------------------------
# Skill / keyword dictionaries used for extraction
# ---------------------------------------------------------------------------

TECH_SKILLS = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "ruby", "go", "golang", "rust", "swift", "kotlin", "php", "r",
        "scala", "perl", "matlab", "dart", "shell", "bash", "powershell",
        "html", "css", "sql", "nosql"
    ],
    "frameworks": [
        "react", "angular", "vue", "next.js", "nextjs", "django", "flask",
        "fastapi", "express", "spring", "spring boot", "node.js", "nodejs",
        ".net", "asp.net", "laravel", "rails", "ruby on rails", "flutter",
        "svelte", "nuxt", "gatsby", "bootstrap", "tailwind", "jquery"
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "sklearn", "opencv", "spacy", "hugging face", "transformers",
        "neural network", "cnn", "rnn", "lstm", "gpt", "bert", "llm",
        "generative ai", "reinforcement learning", "xgboost", "lightgbm",
        "random forest", "svm", "clustering", "regression", "classification"
    ],
    "data": [
        "pandas", "numpy", "matplotlib", "seaborn", "plotly", "tableau",
        "power bi", "excel", "spark", "hadoop", "hive", "kafka",
        "airflow", "etl", "data pipeline", "data warehouse", "snowflake",
        "bigquery", "redshift", "databricks", "dbt"
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
        "oracle", "cassandra", "dynamodb", "firebase", "elasticsearch",
        "neo4j", "mariadb", "couchdb"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "jenkins", "ci/cd", "terraform", "ansible", "linux", "nginx",
        "apache", "github actions", "gitlab ci", "circleci", "heroku",
        "vercel", "netlify", "cloudflare"
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "postman", "swagger", "figma", "vs code", "intellij", "jupyter",
        "colab", "docker compose"
    ]
}

SOFT_SKILLS_KEYWORDS = [
    "leadership", "teamwork", "communication", "problem solving",
    "problem-solving", "analytical", "collaboration", "adaptability",
    "creative", "creativity", "critical thinking", "time management",
    "project management", "agile", "scrum", "mentoring", "presentation"
]

EDUCATION_PATTERNS = [
    r"(b\.?tech|b\.?e\.?|bachelor|bsc|b\.sc)",
    r"(m\.?tech|m\.?e\.?|master|msc|m\.sc|mba)",
    r"(ph\.?d|doctorate)",
    r"(diploma|associate)",
    r"(computer science|information technology|electronics|electrical|mechanical|data science|artificial intelligence|software engineering)",
    r"(university|institute|college|school|iit|nit|iiit|bits)"
]

DEGREE_LEVELS = {
    "phd": 5, "doctorate": 5,
    "mtech": 4, "msc": 4, "master": 4, "mba": 4, "me": 4,
    "btech": 3, "bsc": 3, "bachelor": 3, "be": 3,
    "diploma": 2, "associate": 2,
    "12th": 1, "high school": 1
}


# ---------------------------------------------------------------------------
# Core extraction functions
# ---------------------------------------------------------------------------

def parse_pdf(file_storage):
    """Extract text from an uploaded PDF file using PyPDF2."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_storage)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"[PDF_ERROR] {str(e)}"


def parse_text(raw_text):
    """Clean raw text resume input."""
    # Normalise whitespace
    text = re.sub(r"\s+", " ", raw_text).strip()
    return text


def _find_skills(text):
    """Return dict of categorised skills found in the resume text."""
    text_lower = text.lower()
    found = {}
    for category, keywords in TECH_SKILLS.items():
        matches = [kw for kw in keywords if kw in text_lower]
        if matches:
            found[category] = list(set(matches))
    return found


def _find_soft_skills(text):
    text_lower = text.lower()
    return [s for s in SOFT_SKILLS_KEYWORDS if s in text_lower]


def _find_education(text):
    """Extract education-related snippets."""
    text_lower = text.lower()
    edu_items = []
    for pattern in EDUCATION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        edu_items.extend(matches)
    return list(set(edu_items))


def _find_projects(text):
    """Heuristically extract project mentions."""
    projects = []
    # Look for lines that follow common patterns
    lines = text.split("\n")
    capture = False
    for line in lines:
        line_stripped = line.strip()
        lower = line_stripped.lower()
        if any(h in lower for h in ["project", "projects"]):
            capture = True
            continue
        if capture:
            if line_stripped and len(line_stripped) > 10:
                # Stop if we hit another section header
                if any(h in lower for h in [
                    "experience", "education", "skill", "certification",
                    "achievement", "award", "hobby", "interest", "reference"
                ]):
                    capture = False
                    continue
                projects.append(line_stripped)
    # Fallback: regex
    if not projects:
        proj_matches = re.findall(
            r"(?:project[s]?\s*:?\s*)(.*?)(?:\n|$)", text, re.IGNORECASE
        )
        projects = [p.strip() for p in proj_matches if len(p.strip()) > 5]
    return projects[:10]  # Cap at 10


def _find_experience(text):
    """Extract years of experience or company mentions."""
    exp = {}
    year_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience)?",
                           text, re.IGNORECASE)
    if year_match:
        exp["years"] = int(year_match.group(1))

    companies = []
    lines = text.split("\n")
    for line in lines:
        lower = line.strip().lower()
        if any(word in lower for word in ["worked at", "intern at", "company",
                                           "employer", "organization"]):
            companies.append(line.strip())
    exp["mentions"] = companies[:5]
    return exp


def _assess_strengths_weaknesses(skills, education, projects, experience):
    """Generate strengths and weaknesses from the profile."""
    strengths = []
    weaknesses = []

    # --- Skills breadth ---
    total_skills = sum(len(v) for v in skills.values())
    if total_skills >= 10:
        strengths.append("Strong and diverse technical skill set")
    elif total_skills >= 5:
        strengths.append("Good foundational technical skills")
    else:
        weaknesses.append("Limited technical skills mentioned — consider expanding your skill set")

    # --- AI/ML ---
    if skills.get("ai_ml"):
        strengths.append(f"AI/ML expertise: {', '.join(skills['ai_ml'][:5])}")
    else:
        weaknesses.append("No AI/ML skills detected — add if relevant to the role")

    # --- Cloud/DevOps ---
    if skills.get("cloud_devops"):
        strengths.append("Cloud & DevOps knowledge is a strong differentiator")
    else:
        weaknesses.append("No cloud/DevOps skills — consider learning AWS/Docker basics")

    # --- Projects ---
    if len(projects) >= 3:
        strengths.append(f"{len(projects)} projects demonstrate hands-on experience")
    elif len(projects) == 0:
        weaknesses.append("No projects detected — interviewers look for practical experience")

    # --- Education ---
    has_degree = any(
        kw in " ".join(education)
        for kw in ["btech", "bachelor", "mtech", "master", "phd", "bsc", "msc"]
    )
    if has_degree:
        strengths.append("Relevant academic background")
    else:
        weaknesses.append("Education details unclear — make sure degree is visible")

    # --- Experience ---
    years = experience.get("years", 0)
    if years >= 3:
        strengths.append(f"{years}+ years of industry experience")
    elif years == 0:
        weaknesses.append("No work experience mentioned — highlight internships if any")

    return strengths, weaknesses


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_profile(text):
    """
    Main entry point. Takes resume text and returns a structured profile dict.

    Returns:
        {
            "skills": { "languages": [...], "frameworks": [...], ... },
            "soft_skills": [...],
            "education": [...],
            "projects": [...],
            "experience": { "years": N, "mentions": [...] },
            "strengths": [...],
            "weaknesses": [...]
        }
    """
    skills = _find_skills(text)
    soft_skills = _find_soft_skills(text)
    education = _find_education(text)
    projects = _find_projects(text)
    experience = _find_experience(text)
    strengths, weaknesses = _assess_strengths_weaknesses(
        skills, education, projects, experience
    )

    return {
        "skills": skills,
        "soft_skills": soft_skills,
        "education": education,
        "projects": projects,
        "experience": experience,
        "strengths": strengths,
        "weaknesses": weaknesses
    }
