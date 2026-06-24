import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Paths
RAW_DB_PATH = "data/raw.db"
STRUCTURED_DB_PATH = "data/structured.db"
LOG_PATH = "logs/pipeline.log"

# Scraping
CONCURRENCY = 10
REQUEST_TIMEOUT = 30
ARXIV_DELAY = 3
PWC_DELAY = 0.5

# Sources
ARXIV_API = "http://export.arxiv.org/api/query"
PWC_API = "https://paperswithcode.com/api/v1"
YC_API = "https://yc-oss.github.io/api/companies/all.json"
PRODUCT_HUNT_API = "https://api.producthunt.com/v2/api/graphql"
REMOTEOK_API = "https://remoteok.com/api"
GITHUB_API = "https://api.github.com/repos"

# LLM
GEMINI_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.1-8b-instant"
DEEPSEEK_MODEL = "deepseek-v4-flash"
GEMINI_LIMIT = 50000
GROQ_LIMIT = 6000
DEEPSEEK_LIMIT = 40000

# Entity Resolution
FUZZY_THRESHOLD = 92

# Sheets
SHEET_NAME = "GraphOne Atlas Intelligence"
TABS = ["Startups", "Products", "Research Papers", "Jobs", "News", "Entity Mapping Log"]
