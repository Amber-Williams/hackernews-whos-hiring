import pandas as pd
import numpy as np
import sqlite3
import os

from lib.data_file import DataFile
from lib.data_extractor_model import DataExtractorModel
from models import JobPostingFormatted
from config import settings
from lib.news_scrapper import NewsScrapper


def save_seen_ids_to_db(seen_ids: set, db_path: str = "jobs.db"):
    """
    Save a set of seen comment IDs to the SQLite database.

    Args:
        seen_ids: Set of comment IDs that have been processed
        db_path: Path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seen_posts (
        comment_id INTEGER PRIMARY KEY
    )
    ''')
    for comment_id in seen_ids:
        try:
            cursor.execute('INSERT OR IGNORE INTO seen_posts (comment_id) VALUES (?)', (comment_id,))
        except sqlite3.Error as e:
            print(f"Error inserting comment ID {comment_id}: {e}")

    conn.commit()
    conn.close()


def get_post_df(extactor_model: DataExtractorModel, year: str, month: str):
    news_scrapper = NewsScrapper(year=year, month=month)
    data_file = DataFile(read_dir=f"./output/{year}/{month}", write_dir=f"./output/{year}/{month}")
    try:
        df = data_file.read_df(file_name="scraped.csv")
        return df
    except FileNotFoundError:
        seen_ids, posts = news_scrapper.get_hn_hiring_posts()
        if len(posts) == 0:
            return None
        df = pd.DataFrame(posts)
        df['token_count'] = df.apply(lambda x: len(extactor_model.get_token_estimate(x['comment_text'])), axis=1)
        data_file.write_df(df=df, file_name="scraped.csv")
        save_seen_ids_to_db(seen_ids)
        return df


def save_job_posting_to_db(job: JobPostingFormatted, db_path: str = "jobs.db"):
    """
    Save a formatted job posting to the SQLite database.

    Args:
        job: The formatted job posting to save
        db_path: Path to the SQLite database file
    """
    db_exists = os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if not db_exists:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_postings (
            post_link_id TEXT PRIMARY KEY,
            post_date TEXT,
            company TEXT,
            job_title TEXT,
            employment_type TEXT,
            salary TEXT,
            remote TEXT,
            city TEXT,
            country TEXT,
            languages_frameworks TEXT,
            remote_rules TEXT,
            how_to_apply TEXT,
            post_username TEXT
        )
        ''')

    cursor.execute('''
    INSERT OR REPLACE INTO jobs (
        post_link_id, post_date, company, job_title, employment_type,
        salary, remote, city, country, languages_frameworks,
        remote_rules, how_to_apply, post_username
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        str(job.get("Post ID")),
        job.get("Post Date"),
        job.get("Company"),
        job.get("Job Title"),
        job.get("Employment Type"),
        job.get("Salary"),
        job.get("Remote"),
        job.get("City"),
        job.get("Country"),
        job.get("Languages and Frameworks"),
        job.get("Remote Rules"),
        job.get("How to Apply"),
        job.get("Post Username")
    ))

    conn.commit()
    conn.close()


def extract_data_from_posts(df: pd.DataFrame, extactor_model: DataExtractorModel, year: str, month: str):
    data_file = DataFile(read_dir=f"./output/{year}/{month}", write_dir=f"./output/{year}/{month}")
    batch_size = df['token_count'].sum() / settings.TOKEN_LIMIT
    batched_df = np.array_split(df, batch_size)
    if len(batched_df) > 30:
        raise ValueError(f"Batch size is too large: {len(batched_df)}")

    success_indices = []
    for index, batch_n_df in enumerate(batched_df):
        try:
            print(f"Processing... batch: {index}")
            request_content = batch_n_df.reset_index().apply(
                lambda row: {
                    "text": row['comment_text'],
                    "comment_id": row['comment_id'],
                    "comment_datetime": row['comment_datetime'],
                    "comment_author": row['comment_author']
                },
                axis=1
            ).tolist()
            jobs = extactor_model.extract(request_content)

            # format batch output and save to job.db
            jobs_formatted = []
            for job in jobs:
                formatted_job = JobPostingFormatted(**job.model_dump()).to_dict()
                jobs_formatted.append(formatted_job)
                save_job_posting_to_db(formatted_job)

            # Create summary batch for markdown
            summary_batch_df = pd.DataFrame(jobs_formatted)
            data_file.write_df(file_name=f"{index}.csv",
                              df=summary_batch_df,
                              partial=True)
            print(f"Saved batch: {index}")
            success_indices.append(index)
        except Exception as e:
            print(f"Unable to parse batch: {index} {e=}...continuing...")
            continue
    # Summary is used for local development only
    data_file.join_partial_df(indices=success_indices, file_name="summary.csv")


def get_month_number(month: str) -> str:
    """Convert month name to two-digit number string."""
    month_map = {
        'january': '01',
        'february': '02',
        'march': '03',
        'april': '04',
        'may': '05',
        'june': '06',
        'july': '07',
        'august': '08',
        'september': '09',
        'october': '10',
        'november': '11',
        'december': '12'
    }
    return month_map[month.lower()]


def get_month_jobs_from_db(year: str, month: str, db_path: str = "jobs.db") -> pd.DataFrame:
    """Get jobs from SQLite database for specific year and month."""
    conn = sqlite3.connect(db_path)
    month_num = get_month_number(month)
    date_pattern = f"{year}-{month_num}-"

    query = """
    SELECT * FROM jobs
    WHERE post_date LIKE ?
    """

    df = pd.read_sql_query(query, conn, params=(f"{date_pattern}%",))
    conn.close()
    return df


def create_report_from_post_data(year: str, month: str):
    """Saves monthly report as a Markdown table"""
    data_file = DataFile(read_dir=f"./output/{year}/{month}",
                         write_dir=f"./table/{year}")
    df = get_month_jobs_from_db(year, month)

    # Reverse mapping to match JobPostingFormatted output that legacy markdown tables use
    df['Post Link'] = df['post_link_id'].apply(
        lambda pid: f"[Post link](https://news.ycombinator.com/item?id={pid})"
    )
    column_mapping = {
        'post_link_id': 'Post ID',
        'post_date': 'Post Date',
        'post_username': 'Post Username',
        'company': 'Company',
        'job_title': 'Job Title',
        'employment_type': 'Employment Type',
        'salary': 'Salary',
        'remote': 'Remote',
        'city': 'City',
        'country': 'Country',
        'languages_frameworks': 'Languages and Frameworks',
        'remote_rules': 'Remote Rules',
        'how_to_apply': 'How to Apply',
    }
    df = df.rename(columns=column_mapping)
    final_columns_order = [
        "Post ID",
        "Post Link",
        "Post Date",
        "Post Username",
        "Company",
        "Job Title",
        "Employment Type",
        "Salary",
        "Remote",
        "City",
        "Country",
        "Languages and Frameworks",
        "Remote Rules",
        "How to Apply",
    ]
    df_final = df[final_columns_order]

    # Save file locally to support legacy DataFile logic
    csv_path = f"{data_file.read_dir}/final_report.csv"
    if not os.path.exists(csv_path):
        os.makedirs(data_file.read_dir, exist_ok=True)
        with open(csv_path, 'w') as f:
            f.write("")
    df_final.to_csv(csv_path, index=False)

    data_file.write_md_from_csv(
        csv_file_name="final_report.csv",
        md_file_name=f"{month}.md"
    )
