import urllib
from bs4 import BeautifulSoup
import requests
import os
import re
from typing import Optional, List

import pandas as pd
import tiktoken

from csv_to_markdown import Csv2Markdown
from config import settings


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
}
OUT_DIR_YEAR = f'./output/{settings.YEAR}'
OUT_DIR = f'{OUT_DIR_YEAR}/{settings.MONTH}'
TABLE_DIR = f'table/{settings.YEAR}'
SUMMARY_FILE = "summary.csv"
SCRAPED_FILE = "scraped.csv"


if not os.path.exists(OUT_DIR_YEAR):
    os.mkdir(OUT_DIR_YEAR)

class DataFiles:
    dir = f"{OUT_DIR}"
    dir_batch = f"{OUT_DIR}/batch"

    def read_df(self, batch: Optional[int] = None, file_name: Optional[str] = None, index_col: Optional[int] = None):
        file_path = f"{self.dir}/{file_name}"
        if batch is not None:
            file_path = f"{self.dir_batch}/{batch}.csv"
        if os.path.exists(file_path):
            return pd.read_csv(file_path, index_col=index_col)
        raise FileNotFoundError(f"File not found: {file_path}")

    def write_df(self, df: pd.DataFrame, batch: Optional[int], file_name: Optional[str]):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        if batch is not None:
            if not os.path.exists(self.dir_batch):
                os.mkdir(self.dir_batch)
            df.to_csv(f"{self.dir_batch}/{batch}.csv")
        elif file_name is not None:
            df.to_csv(f"{self.dir}/{file_name}")

    def read_scraped_df(self):
        return self.read_df(batch=None, file_name=SCRAPED_FILE, index_col=0)

    def read_summary_df(self):
        return self.read_df(batch=None, file_name=SUMMARY_FILE, index_col=0)

    def write_scraped_df(self, df: pd.DataFrame):
        self.write_df(df=df, batch=None, file_name=SCRAPED_FILE)
        return df

    def write_summary_df(self, processed_batches: List[int]):
        # Join batch CSVs into one CSV
        batch_csvs = []
        for batch in processed_batches:
            batch_df = self.read_df(batch=batch, file_name=None, index_col=0)
            batch_csvs.append(batch_df)
        df = pd.concat(batch_csvs)
        df = df.reset_index(drop=True)
        self.write_df(df=df, batch=None, file_name=SUMMARY_FILE)
        return df

    def write_summary_md(self):
        if not os.path.exists(TABLE_DIR):
            os.mkdir(TABLE_DIR)

        csv_file = f"{self.dir}/{SUMMARY_FILE}"
        output_file = f"{TABLE_DIR}/{settings.MONTH}.md"
        md = Csv2Markdown(filepath=csv_file)
        md.save_table(output_file)


def get_hn_next_page(soup, job_posting_comments: List[dict]):
    if soup.find(class_='morelink'):
        next_url = soup.find(class_='morelink')
        next_url = next_url['href']
        response = requests.get(f"https://news.ycombinator.com/{next_url}",
                                headers=headers,
                                timeout=30
                                )
        soup = BeautifulSoup(response.text, 'lxml')
        comments = soup.find_all(class_="comtr")
        for comment_el in comments:
            comment = comment_el.find(class_="commtext")
            # Skip if comment was deleted
            if comment is None:
                continue
            # We only care about comments with a pipe character
            # because it is in the format outlined by HN's whoishiring
            if "|" in comment.text:
                job_posting_comments.append({
                    "comment_text": comment.text,
                    "comment_id": comment_el['id']
                })
        return get_hn_next_page(soup, job_posting_comments)
    else:
        return dict


def scrape_hn_hiring_to_dict():
    # Get the first link from Google search results
    text = f":news.ycombinator.com who's hiring {settings.MONTH} {settings.YEAR}"
    text = urllib.parse.quote_plus(text)
    url = 'https://google.com/search?q=' + text
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    # Scrape the HN thread - page 1
    url = soup.find_all(class_='g')[0]
    url = url.find('a')
    url = url['href']
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    job_posting_comments = []
    comments = soup.find_all(class_="comtr")
    for comment_el in comments:
        comment = comment_el.find(class_="commtext")
        # Skip if comment was deleted
        if comment is None:
            continue
        # We only care about comments with a pipe character
        # because it is in the format outlined by HN's whoishiring
        if "|" in comment.text:
            job_posting_comments.append({
                "comment_text": comment.text,
                "comment_id": comment_el['id']
            })

    # Continue to scrape the HN thread - pages
    get_hn_next_page(soup, job_posting_comments)
    return job_posting_comments


def count_tokens(df):
    encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
    df['token_count'] = df.apply(lambda x: len(encoding.encode(x['comment_text'])), axis=1)
    return df


def str_has_num(string: str):
    return any(char.isdigit() for char in string)
