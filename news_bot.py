import argparse
import yaml
import signal
import sys
import asyncio
import datetime
import time
import random
import re
from bot import Bot as DiscordBot
from icon_manager import IconManager
from logger import Logger
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError
from typing import Optional
from yaml.parser import ParserError
from news.feeds import CodeProject
from yaml.reader import Reader


class NewsBot:
    def __init__(self, args):
        self._args = args
        self._config = self._load_yaml(self._args.config)
        self._imgur_client = self._get_imgur_client(self._args.imgur)
        self._icon_manager = IconManager(self._imgur_client, self._load_yaml(self._args.icons),
                                         self._config["user_agent"])
        self._logger = Logger.get_logger()
        self._is_active = True
        self._feeds = [CodeProject()]
        self._loop = asyncio.get_event_loop()

    def __del__(self):
        self.save()

    def run(self):
        """
        Runs the news bot.
        """
        self._logger.info('NewsBot start')
        self._loop.create_task(self._handle_graceful_terminate())
        self._loop.run_until_complete(self.collect_news())

    def on_signal(self, sig_id: int, frame):
        """
        Catches system signals.
        :param sig_id: The signal unique id that was caught.
        :param frame: The frame of the signal.
        """
        if sig_id != signal.SIGINT:
            return

        self._is_active = False
        self.save()
        sys.exit(0)

    def save(self):
        """
        Saves the bot configuration.
        """
        self._icon_manager.save(self._args.icons)
        with open(self._args.config, 'w+') as config_file:
            yaml.dump(self._config, config_file)

    async def collect_news(self):
        """
        Actively collects the news at a preconfigured period from the available news feeds.
        """
        while self._is_active:
            self._logger.info("Collecting news")
            self._invalidate_cache()

            for feed in self._feeds:
                self._logger.info("Processing feed", feed=feed)
                items = feed.get(self._config["user_agent"], datetime.datetime.today().date())

                self._logger.info("Feed processed", feed=feed, item_count=len(items))
                await self._handle_feed(feed, items)

            await asyncio.sleep(self._config["probe_news_delay"])

    async def _handle_feed(self, feed, items):
        """
        Handles the feed and processes its items for posting.
        :param feed: The processed feed.
        :param items: The items to process which were pulled from the feed.
        """
        item_cache = self._config['cache']['items']

        self._logger.debug("Creating batch", feed=feed, item_count=len(items))
        batch_color = random.Random(datetime.datetime.today().date().__hash__()).randint(0x0, 0xFFFFFF)
        batch = []
        for item in [x for x in items if x.url not in item_cache]:
            self._logger.debug("Adding to batch", batch_len=len(batch), item=item)
            batch.append(item.to_embed(batch_color, self._icon_manager, f'{feed} @ {item.date}'))
            item_cache.append(item.url)

        if batch:
            self._logger.info("Queuing new items for posting", item_count=len(batch))
            await DiscordBot(self._args.token, self._config).run(batch)
        else:
            self._logger.info("No new items for posting, skipping batch", feed=feed)

    async def _handle_graceful_terminate(self):
        """
        Handle graceful termination, this task is here to give cpu runtime to handle signals and other system events.
        """
        while self._is_active:
            await asyncio.sleep(1.0)

    def _invalidate_cache(self):
        """
        Invalidates the cache if it's too old or missing.
        """
        cache = self._config.get('cache', {'timestamp': time.time(), 'items': []})
        today = datetime.datetime.today().date()
        cache_ts = datetime.date.fromtimestamp(cache.get('timestamp', 0))

        if today > cache_ts:
            self._logger.info("Item cache is outdated, clearing", ts=cache_ts)
            cache['timestamp'] = time.time()
            cache['items'] = []

        self._config['cache'] = cache

    @staticmethod
    def _get_imgur_client(client_id) -> Optional[ImgurClient]:
        """
        Creates the imgur client instance.
        :param client_id: The imgur developer client id to be used.
        :return: The ImgurClient, or None if the client id is not accepted.
        """
        try:
            return ImgurClient(client_id, None)
        except ImgurClientError:
            return None

    @staticmethod
    def _load_yaml(file_path) -> Optional[dict]:
        """
        Loads the YAML file.
        :param file_path: The file path of the YAML file.
        :return: The parsed YAML data, or None if the loading fails.
        """
        # Avoid a bug with special characters in PyYAML.
        yaml.reader.Reader.NON_PRINTABLE = re.compile(
            u'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')

        try:
            with open(file_path, 'r', encoding='utf-8') as config_file:
                return yaml.load(config_file.read())
        except ParserError:
            return None
        except FileNotFoundError:
            return None


def main():
    args = argparse.ArgumentParser(prog="NewsBot")
    args.add_argument('--token', help='The bot token to be used to authenticate against discord', required=True)
    args.add_argument('--imgur', help='The imgur client id to be used for uploading the .ico')
    args.add_argument('--config', help='The config file that contains most of the settings', required=True)
    args.add_argument('--icons', help='The icons cache file', required=True)
    args.add_argument('--debug', help='Sets the logger to output debug into console',
                      required=False, action='store_true')

    args = args.parse_args()
    Logger.IS_DEBUG = args.debug

    news_bot = NewsBot(args)
    signal.signal(signal.SIGINT, news_bot.on_signal)
    news_bot.run()
