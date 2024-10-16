from fastapi import FastAPI
import requests
import os
import mariadb
from fastapi.responses import JSONResponse
from fastapi import status

app = FastAPI()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'justthetea')
}

# List of repos to fetch PRs from
REPOS = [
    "justworkshr/clockwork_web",
    "justworkshr/clockface",
    "justworkshr/ieor-payroll-tuning-dashboard",
    "justworkshr/benefits-ops-dash",
    "justworkshr/benefits-ops-api",
    "justworkshr/cs-dash",
    "justworkshr/crimsonsage-product",
    "justworkshr/cdms",
    "justworkshr/paytax-internal",
    "justworkshr/ai-hive-2",
    "justworkshr/tangerine-hive-streamlit",
    "justworkshr/memco",
    "justworkshr/clockwork_mobile",
]

def summarize_titles(titles):
    return f"This week, {len(titles)} PRs were closed."

@app.get("/digest")
def get_digest():
    try:
        response = requests.get(
            'https://api.github.com/repos/justworkshr/clockwork_web/pulls',
            headers=HEADERS,
            params={'state': 'closed', 'per_page': 5}
        )
        prs = response.json()
        titles = [pr['title'] for pr in prs]
        summary = summarize_titles(titles)
        return {"message": summary}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An error occurred."}
        )

@app.get("/db-test")
def test_db_connection():
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        return {"message": "Database connection successful", "result": result}
    except mariadb.Error as e:
        return {"message": f"Error connecting to MariaDB: {e}"}
