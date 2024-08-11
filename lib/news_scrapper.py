import urllib
import requests
from typing import List

from bs4 import BeautifulSoup

class NewsScrapper:
    def __init__(self, year: int, month: str):
        self.headers = {    
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
            }
        self.year = year
        self.month = month

    def _get_page_comments(self, soup, comment_list: List[dict]):
        comments = soup.find_all(class_="comtr")
        for comment_el in comments:
            comment = comment_el.find(class_="commtext")
            # Skip if comment was deleted
            if comment is None:
                continue
            # We only care about comments with a pipe character
            # because it is in the format outlined by HN's whoishiring
            if "|" in comment.text:
                comment_list.append({
                    "comment_text": comment.text,
                    "comment_id": comment_el['id']
                })
        return comment_list

    def _get_next_page(self, soup, comment_list: List[dict]):
        if soup.find(class_='morelink'):
            next_url = soup.find(class_='morelink')
            next_url = next_url['href']
            response = requests.get(f"https://news.ycombinator.com/{next_url}",
                                    headers=self.headers,
                                    timeout=30
                                    )
            soup = BeautifulSoup(response.text, 'lxml')
            _comment_list = self._get_page_comments(soup, comment_list)
            return self._get_next_page(soup, _comment_list)
        else:
            return comment_list

    def get_hn_hiring_posts(self):
        # Get the first link from Google search results
        text = f":news.ycombinator.com who's hiring {self.month} {self.year}"
        text = urllib.parse.quote_plus(text)
        url = 'https://google.com/search?q=' + text
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')

        # Scrape the HN thread
        url = soup.find_all(class_='g')[0]
        url = url.find('a')
        url = url['href']
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        comment_list = []
        comment_list = self._get_page_comments(soup, comment_list)
        # Continue to scrape the HN thread - pages
        return comment_list
