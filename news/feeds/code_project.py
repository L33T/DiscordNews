import requests
import datetime
from lxml import html
from news.item import NewsItem
from news.feed import NewsFeed
from typing import List, Optional


class CodeProject(NewsFeed):
    def get(self, ua: str, min_date: datetime.date, raw: bytes = None, url: bytes = None, *args, **kwargs) \
            -> Optional[List[NewsItem]]:
        """
        Gets the news items from the feed.
        :param ua: The user agent to be used in the request.
        :param min_date: The minimum date accepted.
        :param raw: A raw bytes string to parse.
        :param url: The URL to retrieve the HTML content from.
        :return: A list of news items.
        """
        if raw:
            return self._pick(self._parse(raw), min_date)

        url = url or 'https://www.codeproject.com/script/News/List.aspx'
        result = requests.get(url, headers={'User-Agent': ua})
        if result and result.status_code == 200:
            return self._pick(self._parse(result.content), min_date)

    @staticmethod
    def _pick(items: List[NewsItem], min_date: datetime.date) -> List[NewsItem]:
        """
        Picks the wanted news items according to the oldest timestamp acceptable.
        :param items: The collected news items.
        :param min_date: The minimum date accepted.
        :return: The picked list of news items.
        """
        picked_items = []
        for item in items:
            item_date = datetime.datetime.strptime(item.date, "%d %b %Y").date()
            if item_date >= min_date:
                picked_items.append(item)
        return picked_items

    @staticmethod
    def _parse(content: bytes) -> List[NewsItem]:
        """
        Parses the HTML content into a list of parsed news items.
        :param content: The HTML content retrieved from the site.
        :return: A list of news items.
        """
        nodes = html.fromstring(content)
        node_items = nodes.xpath('//table[@class="feature news"]//tr')[1:]
        items = []
        for item in node_items:
            title = item.xpath('.//td//div[@class="hover-container"]//a[@class="NewsHL"]')
            subtitle = item.xpath('.//td//div[@class="hover-container"]//div[@class="NewsBL"]')
            metadata = item.xpath('.//td[@class="small-text"]')
            url = item.xpath('.//td[@class="small-text"]//a')

            if not title or not subtitle or len(metadata) != 4 or not url:
                continue

            item_type, date, clicks = [metadata[0].text, metadata[2].text, metadata[3].text]

            if item_type == 'Hot Threads':
                continue

            items.append(NewsItem(title[0].text, subtitle[0].text.strip(), url[0].get('href'), url[0].text, item_type,
                                  date))
        return items

    def __repr__(self):
        return "CodeProject"
