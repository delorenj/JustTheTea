from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import mariadb
from fastapi.responses import JSONResponse
from fastapi import status
import random
from datetime import datetime, timedelta, timezone
import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from fastapi import HTTPException
import logging
import json
import sys
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert

print("Starting application...", flush=True)
sys.stdout.flush()
sys.stderr.flush()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
logger.debug(f"GitHub Token: {GITHUB_TOKEN}")
app = FastAPI()

# At the top of the file, after the imports and logging setup
logger.info("Application starting...")

# Enable CORS
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]

# In development, allow all origins
if os.environ.get("ENVIRONMENT") == "development":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'just-the-tea')
}

DATABASE_URL = f"mysql+aiomysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
JUSTWORKS_HR = "justworkshr"
NEON_MOOSE = "neonmoose"
BASE_REPO_URL = "https://api.github.com/repos/{ORG_REPO}/{REPO}/pulls"

# Async engine for asynchronous operations
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# SQLAlchemy model for pull requests
Base = declarative_base()

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String(255))
    pr_number = Column(Integer)
    title = Column(String(255))
    author_login = Column(String(255))
    created_at = Column(DateTime)
    closed_at = Column(DateTime)
    diff = Column(Text)

    __table_args__ = (UniqueConstraint('repo_name', 'pr_number', name='uix_repo_pr'),)

# Create the database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Base Indexer class
class Indexer:
    async def index(self):
        raise NotImplementedError

# PRIndexer extending Indexer
class PRIndexer(Indexer):
    async def index_repo(self, repo: str, start_date: datetime, end_date: datetime, session: AsyncSession):
        page = 1
        per_page = 100
        total_indexed = 0

        while True:
            try:
                url = f'{BASE_REPO_URL.format(ORG_REPO=JUSTWORKS_HR, REPO=repo)}'
                logger.debug(f"Requesting URL: {url}")
                
                response = requests.get(
                    url,
                    headers=HEADERS,
                    params={
                        'state': 'closed',
                        'sort': 'updated',
                        'direction': 'desc',
                        'per_page': per_page,
                        'page': page,
                    }
                )
                response.raise_for_status()
                data = response.json()

                logger.debug(f"Received {len(data)} PRs for repo {repo}")

                if not data:
                    logger.info(f"No more data for repo {repo}. Total PRs indexed: {total_indexed}")
                    break

                for pr in data:
                    closed_at_str = pr.get('closed_at')
                    if not closed_at_str:
                        logger.warning(f"PR {pr.get('number')} has no closed_at date. Skipping.")
                        continue

                    closed_at = datetime.strptime(closed_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                    if closed_at < start_date.replace(tzinfo=timezone.utc):
                        logger.info(f"Reached PR older than start date for repo {repo}. Total PRs indexed: {total_indexed}")
                        await session.commit()  # Commit any remaining changes
                        return

                    if start_date.replace(tzinfo=timezone.utc) <= closed_at <= end_date.replace(tzinfo=timezone.utc):
                        diff_url = pr.get('diff_url')  # Use 'diff_url' instead of 'url'
                        logger.debug(f"Fetching diff from URL: {diff_url}")
                        diff_text = ''
                        if diff_url:
                            try:
                                diff_response = requests.get(diff_url, headers=HEADERS)
                                diff_response.raise_for_status()
                                diff_text = diff_response.text
                                logger.info(f"Successfully fetched diff for PR #{pr.get('number')} in repo {repo}")
                            except requests.RequestException as e:
                                logger.warning(f"Failed to fetch diff for PR #{pr.get('number')} in repo {repo}: {str(e)}")
                                logger.warning(f"Response status code: {diff_response.status_code}")
                                logger.warning(f"Response content: {diff_response.text[:200]}...")  # Log first 200 characters of response

                        # Use insert ... on duplicate key update
                        stmt = insert(PullRequest).values(
                            repo_name=repo,
                            pr_number=pr.get('number'),
                            title=pr.get('title'),
                            author_login=pr.get('user', {}).get('login'),
                            created_at=datetime.strptime(pr.get('created_at', ''), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc),
                            closed_at=closed_at,
                            diff=diff_text,
                        )
                        stmt = stmt.on_duplicate_key_update(
                            title=stmt.inserted.title,
                            author_login=stmt.inserted.author_login,
                            created_at=stmt.inserted.created_at,
                            closed_at=stmt.inserted.closed_at,
                            diff=stmt.inserted.diff,
                        )
                        await session.execute(stmt)
                        total_indexed += 1
                        logger.info(f"Indexed PR #{pr.get('number')} for repo {repo}")
                    else:
                        logger.debug(f"PR #{pr.get('number')} is outside the date range. Skipping.")

                await session.commit()
                logger.info(f"Committed batch of {len(data)} PRs to database for repo {repo}. Total indexed so far: {total_indexed}")

                page += 1
            except Exception as e:
                logger.error(f"Error processing PRs for repo {repo}: {str(e)}")
                logger.exception("Exception details:")
                await session.rollback()
                break

        logger.info(f"Finished indexing repo {repo}. Total PRs indexed: {total_indexed}")

    async def index_all_repos(self, repos: List[str], start_date: datetime, end_date: datetime):
        async with AsyncSessionLocal() as session:
            tasks = [self.index_repo(repo, start_date, end_date, session) for repo in repos]
            await asyncio.gather(*tasks)

# Endpoint to index a single repository
class IndexRepoRequest(BaseModel):
    repo: str
    start_date: str
    end_date: str

@app.post("/api/index-repo")
async def index_repo(request: IndexRepoRequest = Body(...)):
    try:
        logger.info(f"Received request to index repo: {request.repo}")
        logger.info(f"Start date: {request.start_date}, End date: {request.end_date}")
        
        await init_db()  # Ensure database tables are created
        pr_indexer = PRIndexer()
        start_dt = datetime.fromisoformat(request.start_date)
        end_dt = datetime.fromisoformat(request.end_date)
        async with AsyncSessionLocal() as session:
            await pr_indexer.index_repo(request.repo, start_dt, end_dt, session)
        return {"status": "success", "message": f"Indexed PRs for {request.repo}"}
    except Exception as e:
        logger.error(f"Error in index_repo endpoint: {str(e)}")
        logger.exception("Exception details:")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to index all repositories
class IndexAllReposRequest(BaseModel):
    start_date: str
    end_date: str

@app.post("/api/index-all-repos")
async def index_all_repos(request: IndexAllReposRequest):
    try:
        await init_db()  # Ensure database tables are created
        pr_indexer = PRIndexer()
        start_dt = datetime.fromisoformat(request.start_date).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(request.end_date).replace(tzinfo=timezone.utc)
        repos = ['clockwork_web', 'clockface']  # Add all your repos here
        
        async with AsyncSessionLocal() as session:
            # Uncomment the next line if you want to clear the table before each run
            # await clear_pull_requests(session)
            
            for repo in repos:
                try:
                    await pr_indexer.index_repo(repo, start_dt, end_dt, session)
                except Exception as e:
                    logger.error(f"Error indexing repo {repo}: {str(e)}")
                    logger.exception("Exception details:")
        
            # Check the number of PRs in the database
            result = await session.execute(sqlalchemy.select(sqlalchemy.func.count()).select_from(PullRequest))
            pr_count = result.scalar_one()
        
        return {
            "status": "success", 
            "message": f"Indexed PRs for all repositories. Total PRs in database: {pr_count}",
            "indexed_repos": repos,
            "date_range": {"start": start_dt.isoformat(), "end": end_dt.isoformat()}
        }
    except Exception as e:
        logger.error(f"Error in index_all_repos endpoint: {str(e)}")
        logger.exception("Exception details:")
        raise HTTPException(status_code=500, detail=str(e))

# Update the get_dashboard endpoint to fetch data from the database
@app.get("/api/dashboard")
async def get_dashboard():
    logger.debug("Fetching dashboard data")
    try:
        async with AsyncSessionLocal() as session:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            result = await session.execute(
                sqlalchemy.select(PullRequest).where(
                    PullRequest.closed_at >= start_date,
                    PullRequest.closed_at <= end_date
                )
            )
            prs = result.scalars().all()

            # Process data as needed
            total_prs = len(prs)
            
            # Here you would calculate other metrics based on the actual data
            # For now, we'll use some placeholder calculations
            merge_conflicts_resolved = total_prs // 3  # Just an example
            lines_of_code = total_prs * 100  # Another example
            average_review_time = 4.5  # Placeholder

            logger.info(f"Dashboard data fetched successfully. Total PRs: {total_prs}")
            return {
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "team_metrics": {
                    "prs_merged": total_prs,
                    "merge_conflicts_resolved": merge_conflicts_resolved,
                    "lines_of_code": lines_of_code,
                    "average_review_time": average_review_time
                },
                "highlights": [
                    {
                        "icon": "📊",
                        "content": f"The team merged {total_prs} pull requests in the last week, showing great productivity!"
                    },
                    {
                        "icon": "💪",
                        "content": f"A total of {lines_of_code} lines of code were changed, demonstrating significant progress in our codebase."
                    }
                ]
            }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        # Fallback to mock data in case of any error
        return get_mock_dashboard_data()

def summarize_titles(titles):
    # Mock implementation for summarize_titles
    return f"This week, {len(titles)} PRs were closed. Some highlights include improved performance, bug fixes, and new feature implementations."

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
        # Fallback to mock data in case of any error
        mock_summary = summarize_titles(["Mock PR 1", "Mock PR 2", "Mock PR 3"])
        return {"message": mock_summary}

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

@app.get("/api/user_preference")
async def get_user_preference():
    return {
        "tea_frequency": random.choice(["Daily", "Weekly", "Fortnightly", "Monthly", "Quarterly"])
    }

@app.post("/api/user_preference")
async def update_user_preference(preference: dict):
    # In a real app, you'd save this to a database
    return {"status": "success", "message": "Preference updated"}

# Move the mock data to a separate function
def get_mock_dashboard_data():
    start_date = datetime(2024, 10, 1)
    end_date = datetime(2024, 10, 14)
    return {
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "team_metrics": {
            "prs_merged": 813,
            "merge_conflicts_resolved": 36,
            "lines_of_code": 9384,
            "average_review_time": 4.5
        },
        "highlights": [
            {
                "icon": "📊",
                "content": "A pull request for the data pipeline refactor managed to update 500+ lines of code while leaving the system completely untouched by merge conflicts. It's as if the changes slipped in, unnoticed, like a magician pulling off a disappearing act in broad daylight. Database queries? Optimized. Load times? Reduced by 20%. The best part? Not a single conflict raised an eyebrow. This is the kind of magic every sprint could use!"
            },
            {
                "icon": "💰",
                "content": "In the dead of night, the payment gateway timeout issue—which had been haunting users and support teams alike—was finally laid to rest. The fix sliced average timeout from 30 seconds to 3 seconds, and not a single 500 error has dared to show its face since. Users are celebrating, support tickets are dwindling, and the dev team responsible is basking in the glow of a job well done."
            }
        ]
    }

@app.get("/api/pr-count")
async def get_pr_count():
    async with AsyncSessionLocal() as session:
        result = await session.execute(sqlalchemy.select(sqlalchemy.func.count()).select_from(PullRequest))
        count = result.scalar_one()
    return {"pr_count": count}

@app.get("/api/debug/prs")
async def debug_prs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(sqlalchemy.select(PullRequest))
        prs = result.scalars().all()
        return {
            "total_prs": len(prs),
            "prs": [
                {
                    "id": pr.id,
                    "repo_name": pr.repo_name,
                    "pr_number": pr.pr_number,
                    "title": pr.title,
                    "author_login": pr.author_login,
                    "created_at": pr.created_at.isoformat(),
                    "closed_at": pr.closed_at.isoformat(),
                    "diff_sample": pr.diff[:200] if pr.diff else "No diff available"
                }
                for pr in prs[:10]  # Limit to first 10 for brevity
            ]
        }

async def clear_pull_requests(session: AsyncSession):
    await session.execute(sqlalchemy.delete(PullRequest))
    await session.commit()
    logger.info("Cleared all entries from the pull_requests table")
