import pandas as pd
import numpy as np
import sqlite3
import os

from lib.data_file import DataFile
from lib.data_extractor_model import DataExtractorModel
from models import JobPostingFormatted
from config import settings
from lib.news_scrapper import NewsScrapper


def get_post_df(extactor_model: DataExtractorModel, year: str, month: str):
    news_scrapper = NewsScrapper(year=year, month=month)
    data_file = DataFile(read_dir=f"./output/{year}/{month}", write_dir=f"./output/{year}/{month}")
    try:
        df = data_file.read_df(file_name="scraped.csv")
        return df
    except FileNotFoundError:
        posts = news_scrapper.get_hn_hiring_posts()
        df = pd.DataFrame(posts)
        df['token_count'] = df.apply(lambda x: len(extactor_model.get_token_estimate(x['comment_text'])), axis=1)
        data_file.write_df(df=df, file_name="scraped.csv")
        return df


def save_job_posting_to_db(job: JobPostingFormatted, db_path: str = "jobs.db"):
    """
    Save a formatted job posting to the SQLite database.

    Args:
        job: The formatted job posting to save
        db_path: Path to the SQLite database file
    """
    # Create database and table if they don't exist
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
    data_file.join_partial_df(indices=success_indices, file_name="summary.csv")


def create_report_from_post_data(year: str, month: str):
    data_file = DataFile(read_dir=f"./output/{year}/{month}",
                         write_dir=f"./table/{year}")
    data_file.write_md_from_csv(csv_file_name="summary.csv", md_file_name=f"{month}.md")


if __name__ == "__main__":
    year = settings.YEAR
    month = settings.MONTH
    print(f"Running for {year} {month}")
    extactor_model = DataExtractorModel(
            model_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL
        )
    post_df = get_post_df(extactor_model=extactor_model, year=year, month=month)
    extract_data_from_posts(df=post_df, extactor_model=extactor_model, year=year, month=month)
    create_report_from_post_data(year=year, month=month)
