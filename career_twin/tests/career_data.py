"""
Static career data — roles, required skills, interview questions, and resource hints.

Edit this file to add new roles, skills, or questions without touching any other module.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Proficiency levels (ordered from lowest to highest)
# ---------------------------------------------------------------------------
PROFICIENCY_LEVELS: List[str] = ["Beginner", "Intermediate", "Advanced"]

# Minimum proficiency level that counts as "matched / strong"
STRONG_THRESHOLD: str = "Intermediate"

# ---------------------------------------------------------------------------
# Career roles and their required skills
# ---------------------------------------------------------------------------
CAREER_ROLES: Dict[str, Dict] = {
    "ai_ml_engineer": {
        "role_name": "AI/ML Engineer",
        "description": "Builds and deploys machine-learning models and AI systems.",
        "required_skills": [
            "Python",
            "Mathematics",
            "Statistics",
            "NumPy/Pandas",
            "Machine Learning",
            "SQL",
            "Git",
            "Projects",
        ],
    },
    "software_developer": {
        "role_name": "Software Developer",
        "description": "Designs and builds software applications.",
        "required_skills": [
            "Python",
            "Data Structures",
            "Algorithms",
            "Git",
            "SQL",
            "APIs",
            "Projects",
        ],
    },
    "data_analyst": {
        "role_name": "Data Analyst",
        "description": "Analyses data to extract business insights.",
        "required_skills": [
            "Python",
            "SQL",
            "Statistics",
            "Pandas",
            "Data Visualization",
            "Excel",
            "Projects",
        ],
    },
    "cybersecurity_analyst": {
        "role_name": "Cybersecurity Analyst",
        "description": "Protects systems and networks from cyber threats.",
        "required_skills": [
            "Networking",
            "Linux",
            "Python",
            "Cybersecurity Fundamentals",
            "Security Tools",
            "Risk Awareness",
            "Projects",
        ],
    },
}

# Convenience list of valid role slugs
ROLE_SLUGS: List[str] = list(CAREER_ROLES.keys())

# ---------------------------------------------------------------------------
# Skill aliases — maps common shorthand to the canonical skill name
# ---------------------------------------------------------------------------
SKILL_ALIASES: Dict[str, str] = {
    "ml": "Machine Learning",
    "ai": "Machine Learning",
    "numpy": "NumPy/Pandas",
    "pandas": "NumPy/Pandas",
    "numpy/pandas": "NumPy/Pandas",
    "ds": "Data Structures",
    "data structures & algorithms": "Data Structures",
    "viz": "Data Visualization",
    "data viz": "Data Visualization",
    "visualization": "Data Visualization",
    "cyber": "Cybersecurity Fundamentals",
    "cybersecurity": "Cybersecurity Fundamentals",
    "security": "Cybersecurity Fundamentals",
    "stats": "Statistics",
    "maths": "Mathematics",
    "math": "Mathematics",
    "api": "APIs",
    "rest api": "APIs",
    "github": "Git",
    "version control": "Git",
}

# ---------------------------------------------------------------------------
# Resource hints — one-line suggestion per skill (lowercase key)
# ---------------------------------------------------------------------------
RESOURCE_HINTS: Dict[str, str] = {
    "python": "Practice on freeCodeCamp or complete Python.org's official tutorial.",
    "mathematics": "Review Khan Academy's linear algebra and calculus courses.",
    "statistics": "Try StatQuest on YouTube for beginner-friendly statistics.",
    "numpy/pandas": "Follow the official Pandas 10-minute tutorial and NumPy quickstart.",
    "machine learning": "Work through Andrew Ng's Machine Learning course on Coursera.",
    "sql": "Practice SQL on SQLZoo or Mode Analytics.",
    "git": "Complete GitHub's 'Introduction to GitHub' free course.",
    "projects": "Build one small end-to-end project and publish it on GitHub.",
    "data structures": "Solve beginner problems on LeetCode or HackerRank.",
    "algorithms": "Study algorithms on CS50 (free Harvard course).",
    "apis": "Build a small REST API with FastAPI or Flask.",
    "pandas": "Follow the official Pandas 10-minute tutorial.",
    "data visualization": "Practice with Matplotlib and Seaborn; try Tableau Public.",
    "excel": "Complete the Excel Skills for Business Specialization on Coursera.",
    "networking": "Study CompTIA Network+ study materials.",
    "linux": "Try Linux commands on OverTheWire's Bandit wargame.",
    "cybersecurity fundamentals": "Complete the Google Cybersecurity Certificate on Coursera.",
    "security tools": "Practice with Wireshark and Nmap in a safe lab environment.",
    "risk awareness": "Read NIST's beginner-friendly cybersecurity framework overview.",
}

RESOURCE_HINTS_DEFAULT: str = "Search for free tutorials on YouTube or freeCodeCamp."

# ---------------------------------------------------------------------------
# Interview question bank
# ---------------------------------------------------------------------------
INTERVIEW_QUESTIONS: Dict[str, List[Dict]] = {
    "ai_ml_engineer": [
        {
            "id": "ai_1",
            "text": "What is the difference between supervised and unsupervised learning?",
            "expected_keywords": ["supervised", "labeled", "unsupervised", "unlabeled", "clustering", "classification"],
        },
        {
            "id": "ai_2",
            "text": "Explain what overfitting means and how you can prevent it.",
            "expected_keywords": ["overfitting", "training", "test", "regularization", "validation", "dropout", "cross-validation"],
        },
        {
            "id": "ai_3",
            "text": "What is a confusion matrix and why is it useful?",
            "expected_keywords": ["confusion matrix", "true positive", "false positive", "precision", "recall", "accuracy"],
        },
        {
            "id": "ai_4",
            "text": "Why do we split data into training and test sets?",
            "expected_keywords": ["training", "test", "generalize", "evaluate", "overfitting", "unseen"],
        },
        {
            "id": "ai_5",
            "text": "What Python libraries do you use for data analysis and why?",
            "expected_keywords": ["pandas", "numpy", "matplotlib", "seaborn", "scikit", "python"],
        },
        {
            "id": "ai_6",
            "text": "Describe a project you have built or would like to build using machine learning.",
            "expected_keywords": ["project", "model", "data", "train", "predict", "result"],
        },
    ],
    "software_developer": [
        {
            "id": "sd_1",
            "text": "What is the difference between a list and a dictionary in Python?",
            "expected_keywords": ["list", "ordered", "dictionary", "key", "value", "index"],
        },
        {
            "id": "sd_2",
            "text": "Explain what version control is and why Git is important.",
            "expected_keywords": ["git", "version", "commit", "branch", "merge", "track", "history"],
        },
        {
            "id": "sd_3",
            "text": "What is an API and how have you used one?",
            "expected_keywords": ["api", "request", "response", "endpoint", "http", "json", "rest"],
        },
        {
            "id": "sd_4",
            "text": "What does Object-Oriented Programming mean to you?",
            "expected_keywords": ["class", "object", "inheritance", "encapsulation", "method", "attribute"],
        },
        {
            "id": "sd_5",
            "text": "How would you debug a program that is producing incorrect output?",
            "expected_keywords": ["debug", "print", "breakpoint", "test", "log", "check", "error"],
        },
        {
            "id": "sd_6",
            "text": "Describe a software project you have worked on or would like to build.",
            "expected_keywords": ["project", "build", "feature", "user", "code", "design"],
        },
    ],
    "data_analyst": [
        {
            "id": "da_1",
            "text": "What is the difference between a LEFT JOIN and an INNER JOIN in SQL?",
            "expected_keywords": ["left join", "inner join", "match", "null", "all rows", "matching rows"],
        },
        {
            "id": "da_2",
            "text": "How do you handle missing data in a dataset?",
            "expected_keywords": ["missing", "null", "drop", "fill", "impute", "mean", "median", "pandas"],
        },
        {
            "id": "da_3",
            "text": "What is the purpose of data visualization?",
            "expected_keywords": ["visualize", "chart", "graph", "trend", "pattern", "insight", "communicate"],
        },
        {
            "id": "da_4",
            "text": "Explain what a pivot table does.",
            "expected_keywords": ["pivot", "summarize", "aggregate", "group", "rows", "columns", "excel"],
        },
        {
            "id": "da_5",
            "text": "What steps would you follow to analyse a new dataset?",
            "expected_keywords": ["explore", "clean", "visualize", "analyse", "statistics", "shape", "describe"],
        },
        {
            "id": "da_6",
            "text": "Describe a data analysis project you have done or would like to do.",
            "expected_keywords": ["data", "analysis", "insight", "result", "chart", "sql", "python"],
        },
    ],
    "cybersecurity_analyst": [
        {
            "id": "ca_1",
            "text": "What is the difference between a virus and a worm?",
            "expected_keywords": ["virus", "worm", "spread", "replicate", "host", "network", "file"],
        },
        {
            "id": "ca_2",
            "text": "What is a firewall and what does it do?",
            "expected_keywords": ["firewall", "network", "block", "traffic", "rule", "port", "filter"],
        },
        {
            "id": "ca_3",
            "text": "Explain what a phishing attack is.",
            "expected_keywords": ["phishing", "email", "fake", "trick", "credentials", "social engineering"],
        },
        {
            "id": "ca_4",
            "text": "What is the principle of least privilege?",
            "expected_keywords": ["least privilege", "access", "minimum", "permission", "role", "need to know"],
        },
        {
            "id": "ca_5",
            "text": "Why is it important to keep software up to date?",
            "expected_keywords": ["patch", "update", "vulnerability", "exploit", "security", "fix"],
        },
        {
            "id": "ca_6",
            "text": "Describe a cybersecurity scenario you have studied or would like to investigate.",
            "expected_keywords": ["attack", "threat", "defence", "incident", "security", "protect", "analyse"],
        },
    ],
}
