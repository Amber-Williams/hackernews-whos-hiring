import urllib
from bs4 import BeautifulSoup
import requests

import pandas as pd


def get_hn_next_page(soup, dict):
    if soup.find(class_='morelink'):
        next_url = soup.find(class_='morelink')
        next_url = next_url['href']
        response = requests.get("https://news.ycombinator.com/"+ next_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        comments = soup.find_all(class_="commtext")
        for comment in comments:
            dict["text"] += [comment.text]
        return get_hn_next_page(soup, dict)
    else:
        return dict


# Get the first link from Google search results
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
}
month = "may"
year = "2023"
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
    

dict = {'text': []}
comments = soup.find_all(class_="commtext")
for comment in comments:
    dict["text"] += [comment.text]

# Continue to scrape the HN thread - pages
get_hn_next_page(soup, dict)

df = pd.DataFrame(dict)
df.to_csv(f"output/hn-hiring-{month}-{year}.csv")
