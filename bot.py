import asyncio
import codecs
from typing import List
from collections import namedtuple
from discord import Client, Embed, HTTPException, Forbidden, NotFound, InvalidArgument, Message, Emoji
from logger import Logger


RoutingInfo = namedtuple('RoutingInfo', ['server', 'channel', 'reactions'])


class Bot(Client):
    _routing_info: List[RoutingInfo]
    _batches: List[List[Embed]]

    def __init__(self, token: str, config, loop=None, **kwargs):
        super().__init__(loop=loop, **kwargs)

        self._token = token
        self._config = config
        self._batch_task = None
        self._batches = []
        self._routing_info = []
        self._logger = Logger.get_logger()

        self.event(self.on_ready)

    async def run(self, batch, *args, **kwargs):
        """
        Runs the bot.
        """
        self._batches.append(batch)
        await self.start(self._token, *args, **kwargs)

    async def logout(self):
        """
        Logs out of Discord and closes all connections.
        """
        await self.close()
        self._is_logged_in.clear()

    async def close(self):
        """
        Closes the connection to discord.
        """
        if self.is_closed:
            return

        if self.ws is not None and self.ws.open:
            self.ws.close()

        await self.http.close()
        self._closed.set()
        self._is_ready.clear()

    async def on_ready(self):
        """
        Ready event, fires once the bot is connected to the discord servers.
        """
        self._logger.info("Connected to discord servers.")

        servers = self._config["servers"]
        for server in [s for s in self.servers if str(s.id) in servers]:
            server_info = servers[str(server.id)]
            channel = next(iter([c for c in server.channels if c.name == server_info["channel"]]), None)
            if not channel:
                self._logger.debug("Channel not found in server.", server=server.name)
                continue

            self._logger.debug("Adding server to posting list", server=server.name, channel=channel.name)
            self._routing_info.append(RoutingInfo(server, channel, server_info["reactions"]))

        self._batch_task = asyncio.ensure_future(self._handle_batches())

    async def _handle_batches(self):
        """
        Actively handles the batches until empty.
        """
        while len(self._batches) > 0:
            batch = self._batches.pop(0)

            for route in self._routing_info:
                try:
                    for item in batch:
                        self._logger.info("Posting item", title=item.title,
                                          server=route.server.name, channel=route.channel.name)
                        msg = await self.send_message(route.channel, embed=item)

                        for reaction in route.reactions:
                            await self._add_reaction(msg, route.server.emojis, reaction)
                except Forbidden:
                    self._logger.error("Improper permissions, unable to send batch", server=route.server.name,
                                       channel=route.channel.name)
                except NotFound:
                    self._logger.error("Channel not found", server=route.server.name, channel=route.channel.name)
                except HTTPException as e:
                    self._logger.error("HTTP error", server=route.server.name, channel=route.channel.name, ex=e)
                except InvalidArgument as e:
                    self._logger.error("Invalid argument", server=route.server.name, channel=route.channel.name, ex=e)

        await self.logout()
        self._logger.info("Disconnected from discord servers.")

    async def _add_reaction(self, message: Message, emojis: List[Emoji], reaction: str):
        """
        Parses the reaction and adds it to the message.
        :param message: The message object, to attach the reaction to.
        :param emojis: The list of custom emojis that belong to the server.
        :param reaction: The reaction data.
        """
        if reaction.startswith(':') and reaction.endswith(':'):
            emoji = next(iter([e for e in emojis if e.name == reaction[1:-1]]), None)
        else:
            emoji = reaction

        reaction_printable = codecs.encode(bytes(reaction, 'utf-8'), 'hex') if len(reaction) == 1 else reaction
        if not emoji:
            self._logger.error("Emoji not found", message=message.id, reaction=reaction_printable)
            return

        try:
            await self.add_reaction(message, emoji)
        except Forbidden:
            self._logger.error("Improper permissions, unable to add reaction", message=message.id,
                               reaction=reaction_printable)
        except NotFound:
            self._logger.error("Emoji not found", message=message.id, reaction=reaction_printable)
        except HTTPException as e:
            self._logger.error("HTTP error", message=message.id, reaction=reaction_printable, ex=e)
        except InvalidArgument as e:
            self._logger.error("Invalid argument", message=message.id, reaction=reaction_printable, ex=e)
