import asyncio
import datetime
import time
import json
from discord import Client
from news.code_project import CodeProject
from logger import Logger
from icon_manager import IconManager


class Bot(Client):
    def __init__(self, token: str, config, icon_manager: IconManager, loop=None, **kwargs):
        super().__init__(loop=loop, **kwargs)

        self._token = token
        self._config = config
        self._icon_manager = icon_manager
        self._channels = []
        self._news_task = None
        self._pull_news = True
        self._last_post_timestamp = config["last_post_timestamp"]
        self._feeds = [CodeProject()]
        self._logger = Logger.get_logger()

        self.event(self.on_ready)

    def run(self, *args, **kwargs):
        """
        Runs the bot.
        """
        super().run(self._token, *args, **kwargs)

    def save(self, target: str):
        """
        Saves the config to a disk file.
        :param target: The target file.
        """
        with open(target, 'w+') as out:
            self._config["last_post_timestamp"] = self._last_post_timestamp
            json.dump(self._config, out)

    async def on_ready(self):
        """
        Ready event, fires once the bot is connected to the discord servers.
        """
        for channel in [c for c in self.get_all_channels() if c.name == self._config["channel"]]:
            if str(channel.server.id) in self._config["servers"]:
                self._logger.debug("Adding channel to posting list", channel=channel.name, server=channel.server.name)
                self._channels.append(channel)

        self._news_task = asyncio.ensure_future(self._handle_news())

    async def _handle_news(self):
        """
        Handle news loop, this task iterates every delay that is taken from the config and probes for new news
        based on the day.
        """
        while self._pull_news:
            today_timestamp = time.mktime(
                datetime.datetime.strptime(datetime.datetime.today().strftime('%d %b %Y'), "%d %b %Y").timetuple())
            self._logger.info("Probing news", today_timestamp=today_timestamp)
            if today_timestamp <= self._last_post_timestamp:
                self._logger.info("Already posted news today, aborting probe.")
                await asyncio.sleep(self._config["probe_news_delay"])
                continue

            for feed in self._feeds:
                self._logger.info("Processing feed", feed=feed)
                items = feed.get(self._config["user_agent"], today_timestamp)
                self._logger.debug("Got items from feed", item_amount=len(items))

                if items:
                    self._logger.debug("Updating last post time", last_post_time=today_timestamp)
                    self._last_post_timestamp = today_timestamp
                for item in items:
                    self._logger.debug("Posting item", name=item.title)
                    # TODO: Match color to category.
                    embed = item.to_embed(0xFF80C0, self._icon_manager, f'{feed} - {item.date}')
                    if embed:
                        for channel in self._channels:
                            self._logger.info("Posting item", name=item.title, channel=channel.name,
                                              server=channel.server.name)
                            await self.send_message(destination=channel, embed=embed)
                    else:
                        self._logger.error("Failed to generate embed for item", name=item.title)

            self._logger.info("Probing news finished.")
            await asyncio.sleep(self._config["probe_news_delay"])
