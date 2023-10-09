import urllib
from bs4 import BeautifulSoup
import requests

import pandas as pd

from csv_to_markdown import Csv2Markdown
from chat_extractor import ChatExtractor


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
}


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


def create_hn_hiring_csv(month, year):
    # Get the first link from Google search results
    text = f":news.ycombinator.com who's hiring {month} {year}"
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

    # Save to CSV
    df = pd.DataFrame(hn_dict)
    df.to_csv(f"output/hn-hiring-{month}-{year}.csv")


def parse_hiring_comment(chatextractor: ChatExtractor, month, year, df, batch):
    if len(df) > 500:
        raise Exception(f"Unable to parse batch: {batch}, too large")
    # Use LLM to organize comment data into a dataframe
    comment_summaries = []
    for index, row in df.iterrows():
        print('Processing row...', index)
        try:
            _row = chatextractor.extract(row['text'])
            if _row is None:
                continue
            if isinstance(_row, list):
                for _r in _row:
                    _r["content"] = row['text']
                    comment_summaries.append(_r)
            else:
                _row["content"] = row['text']
                comment_summaries.append(_row)
        except Exception as err:
            print(f"Unable to parse batch: {batch} row: {index}, {err=}")
            continue

    # Save to CSV
    comment_summaries_df = pd.DataFrame.from_dict(comment_summaries)
    comment_summaries_df.to_csv(f"output/hn-hiring-{month}-{year}-summary-{batch}.csv")


def join_batch_csvs(month, year, batch_size: int):
    # Join batch CSVs into one CSV
    batch_csvs = []
    for i in range(batch_size):
        batch_csvs.append(pd.read_csv(f"output/hn-hiring-{month}-{year}-summary-{i}.csv", index_col=0))
    df = pd.concat(batch_csvs)
    df.reset_index(drop=True).to_csv(f"output/hn-hiring-{month}-{year}-summary.csv")


def drop_time_wasters(month, year):
    df = pd.read_csv(f"output/hn-hiring-{month}-{year}-summary.csv")
    df = df[['salary', 'job title', 'company', 'company location', 'link to apply', 'remote']]
    df = df[df['salary'].notna()]
    df = df[df['salary'] != 'Not mentioned']
    df.reset_index(drop=True).to_csv(f"output/hn-hiring-{month}-{year}-summary-filtered.csv")


def turn_into_markdown(month, year):
    md = Csv2Markdown(f"output/hn-hiring-{month}-{year}-summary-filtered.csv")
    md.save_table(f"table/hn-hiring-{month}-{year}.md")
