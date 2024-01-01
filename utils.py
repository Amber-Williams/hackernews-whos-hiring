import urllib
from bs4 import BeautifulSoup
import requests
import os
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
CLEAN_FILE = "clean.csv"
SUMMARY_FILE = "summary.csv"
SCRAPED_FILE = "scraped.csv"


if not os.path.exists(OUT_DIR_YEAR):
    os.mkdir(OUT_DIR_YEAR)


class DataFiles:
    dir = f"{OUT_DIR}"
    dir_batch = f"{OUT_DIR}/batch"

    def read_df(self, batch: Optional[int], file_name: Optional[str], index_col: Optional[int] = None):
        if batch is not None:
            file_path = f"{self.dir_batch}/{batch}.csv"
            if os.path.exists(file_path):
                return pd.read_csv(file_path, index_col=index_col)
            raise FileNotFoundError(f"File not found: {file_path}")

        return pd.read_csv(f"{self.dir}/{file_name}", index_col=index_col)

    def write_df(self, df: pd.DataFrame, batch: Optional[int], file_name: Optional[str]):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        if batch is not None:
            if not os.path.exists(self.dir_batch):
                os.mkdir(self.dir_batch)
            df.to_csv(f"{self.dir_batch}/{batch}.csv")
        elif file_name is not None:
            df.to_csv(f"{self.dir}/{file_name}")

    def write_scraped_df(self, df: pd.DataFrame):
        # saves scraped data to csv
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

    def write_cleaned_df(self, df: pd.DataFrame):
        df = df[['salary', 'job title', 'company', 'company location', 'link to apply', 'remote', 'text']]
        # Filter out rows where 'salary' does not contain at least one number
        df = df[df['salary'].str.contains(r'\d', na=False)]
        df = df.reset_index(drop=True)

        # clean csv save
        self.write_df(df=df, batch=None, file_name=CLEAN_FILE)

        # clean markdown save
        clean_file = os.path.join(OUT_DIR, CLEAN_FILE)
        md = Csv2Markdown(filepath=clean_file)
        if not os.path.exists(TABLE_DIR):
            os.mkdir(TABLE_DIR)
        md.save_table(f"{TABLE_DIR}/{settings.MONTH}.md")


def get_hn_next_page(soup, dict):
    if soup.find(class_='morelink'):
        next_url = soup.find(class_='morelink')
        next_url = next_url['href']
        response = requests.get("https://news.ycombinator.com/"+ next_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        comments = soup.find_all(class_="commtext")
        for comment in comments:
            if "|" in comment.text:
                dict["text"] += [comment.text]
        return get_hn_next_page(soup, dict)
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
    hn_dict = {'text': []}
    comments = soup.find_all(class_="commtext")
    for comment in comments:
        if "|" in comment.text:
            hn_dict["text"] += [comment.text]

    # Continue to scrape the HN thread - pages
    get_hn_next_page(soup, hn_dict)
    return hn_dict


def count_tokens(df):
    encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
    df['token_count'] = df.apply(lambda x: len(encoding.encode(x['text'])), axis=1)
    return df


def str_has_num(string: str):
    return any(char.isdigit() for char in string)
