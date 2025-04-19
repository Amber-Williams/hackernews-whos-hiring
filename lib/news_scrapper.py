import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from bs4 import BeautifulSoup
import sqlite3

class NewsScrapper:
    def __init__(self, year: int, month: str):
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
            }
        self.year = year
        self.month = month

    def get_hn_hiring_thread_id(self):
        # Get the whoishiring submissions page
        url = 'https://news.ycombinator.com/submitted?id=whoishiring'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')

        # Find the "Who is hiring?" post for the specified month and year
        target_title = f"Ask HN: Who is hiring? ({self.month} {self.year})"
        links = soup.find_all('a')
        hiring_link = None

        for link in links:
            if link.text == target_title:
                hiring_link = link['href']
                break

        if not hiring_link:
            raise Exception(f"Could not find hiring post for {self.month} {self.year}")

        url = f"https://news.ycombinator.com/{hiring_link}"
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        thread_id = query_params.get('id', [None])[0]

        if not thread_id:
            raise Exception(f"Could not find thread id for {self.month} {self.year}")

        return thread_id

    def filter_unseen_posts(self, post_ids):
        """
        Filter out post IDs that already exist in the seen_posts table of the jobs.db database.

        Args:
            post_ids: A list or set of post IDs to filter

        Returns:
            A list containing only the post IDs that haven't been seen before
        """

        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seen_posts'")
        if not cursor.fetchone():
            conn.close()
            return list(post_ids)

        placeholders = ','.join(['?'] * len(post_ids))

        query = f"SELECT comment_id FROM seen_posts WHERE comment_id IN ({placeholders})"
        cursor.execute(query, list(post_ids))
        seen_ids = {row[0] for row in cursor.fetchall()}
        conn.close()

        return [post_id for post_id in post_ids if post_id not in seen_ids]

    def get_hn_hiring_posts(self):
        comment_list = []
        seen_comment_ids = set()
        thread_id = self.get_hn_hiring_thread_id()

        # Get the hiring thread
        response = requests.get(
            url=f"https://hacker-news.firebaseio.com/v0/item/{thread_id}.json",
            headers=self.headers,
            timeout=30
            )
        data = response.json()
        thread_kids = data['kids']
        thread_kids = self.filter_unseen_posts(thread_kids)

        # Get level 1 comments
        for kid in thread_kids:
            seen_comment_ids.add(kid)

            response = requests.get(
                url=f"https://hacker-news.firebaseio.com/v0/item/{kid}.json",
                headers=self.headers,
                timeout=30
                )
            kid_data = response.json()
            html_content = kid_data.get("text", "")

            if not html_content or "|" not in html_content:
                continue

            # inject full links into text as HN shortens links with ellipses after 60 characters
            soup = BeautifulSoup(html_content, 'lxml')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    link.replace_with(href)
                else:
                    link.unwrap()
            plain_text = soup.get_text(separator='\n', strip=True)
            comment_datetime = datetime.fromtimestamp(data['time']).strftime('%Y-%m-%dT%H:%M:%S')

            comment_list.append({
                "comment_text": plain_text,
                "comment_id": kid,
                "comment_datetime": comment_datetime,
                "comment_author": kid_data['by'],
            })

        return seen_comment_ids, comment_list
