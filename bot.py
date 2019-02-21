import asyncio
from typing import List, Any

from discord import Client, Embed, Channel
from logger import Logger


class Bot(Client):
    _channels: List[Channel]
    _batches: List[List[Embed]]

    def __init__(self, token: str, config, loop=None, **kwargs):
        super().__init__(loop=loop, **kwargs)

        self._token = token
        self._config = config
        self._batch_task = None
        self._batches = []
        self._channels = []
        self._logger = Logger.get_logger()

        self.event(self.on_ready)

    async def run(self, batch, *args, **kwargs):
        """
        Runs the bot.
        """
        self._batches.append(batch)
        await self.start(self._token, *args, **kwargs)

    async def on_ready(self):
        """
        Ready event, fires once the bot is connected to the discord servers.
        """
        self._logger.info("Connected to discord servers.")

        for channel in [c for c in self.get_all_channels() if c.name == self._config["channel"]]:
            if str(channel.server.id) in self._config["servers"]:
                self._logger.debug("Adding channel to posting list", channel=channel.name, server=channel.server.name)
                self._channels.append(channel)

        self._batch_task = asyncio.ensure_future(self._handle_batches())

    async def _handle_batches(self):
        """
        Actively handles the batches until empty.
        """
        while len(self._batches) > 0:
            batch = self._batches.pop(0)
            for channel in self._channels:
                server = channel.server
                for embed_item in batch:
                    self._logger.info("Posting item", title=embed_item.title, server=server.name, channel=channel.name)
                    await self.send_message(channel, embed=embed_item)

        await self.logout()
        self._logger.info("Disconnected from discord servers.")
