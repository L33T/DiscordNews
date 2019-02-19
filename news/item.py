from discord import Embed
from urllib.parse import urlparse
from icon_manager import IconManager


class NewsItem:
    def __init__(self, title, subtitle, url, source, item_type, date):
        self.title = title
        self.subtitle = subtitle
        self.url = url
        self.source = source
        self.item_type = item_type
        self.date = date

    def to_embed(self, color: int, icon_mgr: IconManager = None, footer: str = None):
        """
        Converts the news item into a discord embed.
        :param color: The color of the embed line.
        :param icon_mgr: The icon manager, for caching purposes.
        :param footer: The footer text of the embed.
        :return: The embed object for posting.
        """
        ico = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(self.url))
        ico = (icon_mgr.get(ico) if icon_mgr else None) or f'{ico}/favicon.ico'
        embed = Embed(title=self.title, description=self.subtitle, color=color)
        embed.set_author(name=self.source, icon_url=ico)
        embed.add_field(name=self.url, value=self.item_type)
        if footer:
            embed.set_footer(text=footer)
        return embed

    def __repr__(self):
        return f'NewsItem(title={self.title}, subtitle={self.subtitle}, url={self.url}, item_type={self.item_type}, ' \
               f'date={self.date})'
