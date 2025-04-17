"""Convert a markdown file's table to a SQLite database.

This script parses job listings from markdown tables and stores them in a SQLite database.
It's currently kept for reference purposes only.

Usage:    python md-to-sqlite-converter.py <markdown_file> [post_date] [output_db_file]

Example:  python md-to-sqlite-converter.py table/2025/March.md "2025-03-01T00:00:00" posts.db
"""

import sqlite3
import sys
import os


def parse_jobs_from_markdown(file_path):
    """
    Parse job listings from a markdown file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    rows = []
    in_table = False

    for line in content.split('\n'):
        line = line.strip()

        if not line:
            continue

        if '---' in line and '|' in line:
            in_table = True
            continue

        if in_table and line.startswith('|') and line.endswith('|'):
            rows.append(line)

    jobs = []
    for idx, row in enumerate(rows):
        cells = [cell.strip() for cell in row.split('|')[1:-1]]

        if len(cells) < 11:
            print(f"Warning: Row {idx+1} has only {len(cells)} cells, skipping.")
            continue

        salary = cells[8]
        if not any(char.isdigit() for char in salary):
            salary = None

        employment_type = cells[7]
        if "unknown" in employment_type.lower():
            employment_type = "full-time"

        location = cells[10]
        city = None
        country = None
        state = None

        if location:
            location_list = location.split(',')
            if len(location_list) == 3 and "US" in location_list[2].strip():
                # handle cases like "Austin, TX, USA"
                city = location_list[0].strip()
                state = location_list[1].strip()
                country = location_list[2].strip()
            elif len(location_list) == 2:
                city = location_list[0].strip()
                country = location_list[1].strip()
            else:
               print(location)
               city = location

            if city and "unknown" in city.lower():
                city = None
            if country and "unknown" in country.lower():
                country = None

        # v3
        job = {
            'post_link_id': cells[1],
            'post_date': cells[3],
            'post_username': cells[4],
            'company': cells[5],
            'job_title': cells[6],
            'employment_type': employment_type,
            'salary': salary,
            'remote': cells[9],
            'city': city,
            'country': country,
            'languages_frameworks': cells[11],
            'remote_rules': cells[12],
            'how_to_apply': cells[13] if len(cells) > 13 else ''
        }
        # v2
        # job = {
        #     'post_link_id': cells[1].split('=')[-1].replace(')', ''),
        #     'company': cells[2],
        #     'job_title': cells[3],
        #     'employment_type': employment_type,
        #     'salary': salary,
        #     'remote': cells[6],
        #     'city': city,
        #     'country': country,
        #     'languages_frameworks': cells[8],
        #     'remote_rules': cells[9],
        #     'how_to_apply': cells[10] if len(cells) > 10 else ''
        # }

        jobs.append(job)

    return jobs


def create_sqlite_database(jobs, db_file, post_date):
    """
    Create a SQLite database from the parsed jobs data.

    Args:
        jobs: List of job dictionaries
        db_file: SQLite database file path
        post_date: Post date as string in format "YYYY-MM-DDThh:mm:ss"
        post_username: Username who posted the job (defaults to empty string)
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute('''
        CREATE TABLE jobs (
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


    # Insert all jobs (we don't clear existing data to allow appending)
    count = 0
    for job in jobs:
        try:
            # Check if this job ID already exists
            cursor.execute("SELECT post_link_id FROM jobs WHERE post_link_id = ?", (job['post_link_id'],))
            exists = cursor.fetchone() is not None

            if exists:
                # Update the existing record
                cursor.execute('''
                UPDATE jobs SET
                    post_link_id = ?, company = ?, job_title = ?, employment_type = ?,
                    salary = ?, remote = ?, city = ?, country = ?, languages_frameworks = ?,
                    remote_rules = ?, how_to_apply = ?, post_date = ?, post_username = ?
                WHERE post_link_id = ?
                ''', (
                    job['post_link_id'], job['company'], job['job_title'],
                    job['employment_type'], job['salary'], job['remote'], job['city'], job['country'],
                    job['languages_frameworks'], job['remote_rules'], job['how_to_apply'],
                    post_date, job.get('post_username', ''), job['post_link_id']
                ))
            else:
                # Insert a new record
                cursor.execute('''
                INSERT INTO jobs (
                    post_link_id, company, job_title, employment_type,
                    salary, remote, city, country, languages_frameworks,
                    remote_rules, how_to_apply, post_date, post_username
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['post_link_id'], job['company'], job['job_title'],
                    job['employment_type'], job['salary'], job['remote'], job['city'], job['country'],
                    job['languages_frameworks'], job['remote_rules'], job['how_to_apply'],
                    post_date, job.get('post_username', '')
                ))
            count += 1
        except sqlite3.Error as e:
            print(f"Error processing job {job['post_link_id']}: {e}")

    conn.commit()
    conn.close()

    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python md-to-sqlite-converter.py <markdown_file> [post_date] [output_db_file]")
        print("Example: python md-to-sqlite-converter.py table/2025/March.md \"2025-03-01T00:00:00\" jobs.db")
        sys.exit(1)

    markdown_file = sys.argv[1]
    post_date = sys.argv[2] if len(sys.argv) > 2 else ""
    db_file = sys.argv[3] if len(sys.argv) > 3 else 'jobs.db'

    if not os.path.exists(markdown_file):
        print(f"Error: File '{markdown_file}' not found.")
        sys.exit(1)

    print(f"Parsing jobs from {markdown_file}...")
    jobs = parse_jobs_from_markdown(markdown_file)
    action = "added/updated"
    jobs_inserted = create_sqlite_database(jobs, db_file, post_date)
    print(f"Successfully {action} {jobs_inserted} jobs in the database.")
    print(f"Post date: {post_date}")


if __name__ == "__main__":
    main()
