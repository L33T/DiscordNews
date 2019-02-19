from abc import abstractmethod
from news.item import NewsItem
from typing import List


class NewsFeed:
    @abstractmethod
    def get(self, ua: str, timestamp: float, *args, **kwargs) -> List[NewsItem]:
        """
        Gets the news items from the feed.
        :param ua: The user agent to be used in the request.
        :param timestamp: The timestamp for the oldest item acceptable.
        :return: A list of news items.
        """
        raise NotImplementedError

    def __repr__(self):
        return ""
