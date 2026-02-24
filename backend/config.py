"""
config.py — Central configuration, constants, skill/domain databases.
All other modules import directly from this file.
"""

import os
from dotenv import load_dotenv

# Load .env from the same backend/ folder
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "").strip()
ADZUNA_APP_ID    = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_API_KEY   = os.getenv("ADZUNA_API_KEY", "").strip()
SMTP_SERVER      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", 587))
SMTP_USER_ENV    = os.getenv("SMTP_USER", "")
SMTP_PASS_ENV    = os.getenv("SMTP_PASS", "")
STARTUP_JOBS_URL = os.getenv("STARTUP_JOBS_URL", "https://startup.jobs/").strip()
GEMINI_MODEL_ENV = os.getenv("GEMINI_MODEL", "").strip()

GEMINI_MODELS = [m for m in [
    GEMINI_MODEL_ENV,
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
] if m]

# ── Experience buckets ────────────────────────────────────────────────────────
EXP_BUCKETS = {
    "Fresher" : ["intern", "trainee", "fresher", "entry level", "graduate", "junior"],
    "0-2 yrs" : ["junior", "associate", "entry level", "0-2 years"],
    "2-4 yrs" : ["mid-level", "2-4 years", "intermediate"],
    "5-10 yrs": ["senior", "lead", "principal", "5+ years"],
}

# ── Indian cities ─────────────────────────────────────────────────────────────
INDIA_LOCATIONS = {
    "hyderabad","bangalore","bengaluru","chennai","mumbai","pune","delhi","noida",
    "gurugram","gurgaon","kolkata","ahmedabad","jaipur","kochi","coimbatore",
    "indore","bhopal","lucknow","chandigarh","vizag","visakhapatnam","remote","india",
}

# ── Skills database ───────────────────────────────────────────────────────────
SKILLS_DB = {
    "python","java","javascript","typescript","c++","c#","c","go","golang","rust",
    "kotlin","swift","scala","r","matlab","perl","php","ruby","dart","julia",
    "html","css","react","reactjs","angular","vue","vuejs","nextjs","nodejs",
    "express","django","flask","fastapi","spring","springboot","asp.net",
    "tailwind","bootstrap","sass","graphql","rest","restful api","websocket",
    "machine learning","deep learning","nlp","natural language processing",
    "computer vision","data science","data analysis","data engineering",
    "tensorflow","pytorch","keras","scikit-learn","sklearn","xgboost","lightgbm",
    "pandas","numpy","matplotlib","seaborn","plotly","opencv","huggingface",
    "transformers","bert","gpt","llm","generative ai","reinforcement learning",
    "sql","mysql","postgresql","mongodb","redis","elasticsearch","cassandra",
    "sqlite","oracle","dynamodb","firebase","supabase","neo4j","bigquery",
    "aws","azure","gcp","google cloud","docker","kubernetes","terraform",
    "jenkins","ci/cd","github actions","ansible","linux","bash","shell",
    "nginx","apache","microservices","serverless","lambda",
    "hadoop","spark","kafka","airflow","dbt","tableau","power bi","looker",
    "excel","snowflake","databricks","hive","flink","redshift",
    "git","github","gitlab","jira","agile","scrum","devops","mlops","api",
    "postman","swagger","figma","selenium","pytest","junit",
    "cybersecurity","cyber security","penetration testing","ethical hacking",
    "network security","siem","soc","vulnerability assessment","owasp",
    "blockchain","web3","solidity","iot","embedded systems","robotics",
    "image processing","signal processing","optimization","statistics",
}

PHRASE_SKILLS = sorted([s for s in SKILLS_DB if " " in s], key=len, reverse=True)
SINGLE_SKILLS = {s for s in SKILLS_DB if " " not in s}

# ── Domain map ────────────────────────────────────────────────────────────────
DOMAIN_MAP = {
    "Machine Learning / AI": {
        "machine learning","deep learning","nlp","computer vision","tensorflow",
        "pytorch","keras","scikit-learn","xgboost","huggingface","transformers",
        "bert","gpt","llm","generative ai","reinforcement learning",
    },
    "Data Science": {
        "data science","data analysis","pandas","numpy","matplotlib","seaborn",
        "tableau","power bi","statistics","bigquery","spark","hadoop",
    },
    "Backend": {
        "python","java","nodejs","django","flask","fastapi","spring","microservices",
        "rest","restful api","sql","postgresql","redis","docker",
    },
    "Frontend": {
        "react","reactjs","angular","vue","vuejs","nextjs","html","css",
        "javascript","typescript","tailwind","bootstrap","figma",
    },
    "Cloud / DevOps": {
        "aws","azure","gcp","docker","kubernetes","terraform","jenkins",
        "ci/cd","ansible","serverless","linux",
    },
    "Data Engineering": {
        "spark","kafka","airflow","dbt","hadoop","snowflake","databricks",
        "hive","flink","redshift","data engineering",
    },
    "Cyber Security": {
        "cybersecurity","cyber security","penetration testing","ethical hacking",
        "network security","siem","soc","owasp",
    },
}

# ── Skill → roles ─────────────────────────────────────────────────────────────
SKILL_TO_ROLES = {
    "python":           ["Python Developer","Backend Engineer"],
    "machine learning": ["Machine Learning Engineer","ML Engineer","AI Engineer"],
    "deep learning":    ["Deep Learning Engineer","AI Researcher"],
    "nlp":              ["NLP Engineer","Computational Linguist"],
    "data science":     ["Data Scientist","Data Analyst"],
    "data analysis":    ["Data Analyst","Business Analyst"],
    "data engineering": ["Data Engineer","ETL Developer"],
    "tensorflow":       ["ML Engineer","AI Engineer"],
    "pytorch":          ["Deep Learning Engineer","ML Researcher"],
    "react":            ["Frontend Developer","React Developer"],
    "nodejs":           ["Backend Developer","Node.js Developer"],
    "django":           ["Django Developer","Python Backend Developer"],
    "sql":              ["Database Administrator","Data Analyst"],
    "aws":              ["Cloud Engineer","AWS Solutions Architect"],
    "docker":           ["DevOps Engineer","Cloud Engineer"],
    "kubernetes":       ["DevOps Engineer","Platform Engineer"],
    "java":             ["Java Developer","Backend Engineer"],
    "cybersecurity":    ["Security Engineer","Penetration Tester"],
    "spark":            ["Data Engineer","Big Data Engineer"],
    "kafka":            ["Data Engineer","Platform Engineer"],
    "llm":              ["AI Engineer","LLM Engineer","GenAI Developer"],
    "generative ai":    ["GenAI Developer","AI Engineer"],
    "blockchain":       ["Blockchain Developer","Web3 Developer"],
    "javascript":       ["Frontend Developer","Full Stack Developer"],
    "typescript":       ["Frontend Developer","Full Stack Developer"],
    "angular":          ["Frontend Developer","Angular Developer"],
    "vue":              ["Frontend Developer","Vue Developer"],
    "go":               ["Backend Engineer","Go Developer"],
    "rust":             ["Systems Engineer","Rust Developer"],
    "scala":            ["Data Engineer","Scala Developer"],
    "c++":              ["Systems Engineer","Embedded Developer"],
    "devops":           ["DevOps Engineer","Platform Engineer"],
    "mlops":            ["MLOps Engineer","ML Platform Engineer"],
}

# ── Domain → companies ────────────────────────────────────────────────────────
DOMAIN_TO_COMPANIES = {
    "Machine Learning / AI": ["Google","Amazon","Microsoft","Meta","Adobe","Zoho","Freshworks","Flipkart","Samsung","Qualcomm"],
    "Data Science":          ["TCS","Infosys","Wipro","Accenture","Capgemini","IBM","Mu Sigma","Latentview Analytics"],
    "Backend":               ["Amazon","Flipkart","Zomato","Swiggy","Paytm","Ola","BrowserStack","Atlassian","Freshworks"],
    "Frontend":              ["Accenture","Capgemini","Wipro","Zoho","BrowserStack","Atlassian"],
    "Cloud / DevOps":        ["Amazon","Microsoft","Google","IBM","Oracle","Bosch"],
    "Data Engineering":      ["Amazon","Microsoft","Google","Databricks","TCS","Infosys"],
    "Cyber Security":        ["Wipro","TCS","IBM","Palo Alto Networks","Aujas"],
}

# ── HTTP headers for scraping ─────────────────────────────────────────────────
SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

ROLE_KEYWORDS = [
    "engineer","developer","analyst","scientist","architect","lead","manager",
    "intern","trainee","associate","consultant","specialist","designer","researcher",
    "devops","mlops","qa","tester","sre","dba","administrator",
]

COUNTRY_MAP = {
    "India": "in", "USA": "us", "UK": "gb", "Canada": "ca", "Australia": "au",
}
