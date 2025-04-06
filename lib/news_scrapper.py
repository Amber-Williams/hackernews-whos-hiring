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
                comment_datetime = comment_el.find(class_="comhead").find(class_="age")
                comment_datetime = comment_datetime.get('title')
                comment_datetime = comment_datetime.split(" ")[0]

                comment_list.append({
                    "comment_text": comment.text,
                    "comment_id": comment_el['id'],
                    "comment_datetime": comment_datetime,
                    "comment_author": comment_el.find(class_="comhead").find(class_="hnuser").text,
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

        # Get the comments from the hiring post
        response = requests.get(f"https://news.ycombinator.com/{hiring_link}",
                              headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        comment_list = []
        comment_list = self._get_page_comments(soup, comment_list)
        # Continue to scrape the HN thread - pages
        return comment_list
