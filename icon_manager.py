import requests
import hashlib
import tempfile
import io
import yaml
import urllib.parse
from PIL import Image
from logger import Logger
from lxml import html
from imgurpython import ImgurClient
from typing import Optional


class IconManager:
    def __init__(self, imgur: ImgurClient, data: dict, user_agent: str):
        self._imgur_client = imgur
        self._hashes = data
        self._user_agent = user_agent
        self._logger = Logger.get_logger()

    def get(self, url: str) -> str:
        """
        Gets and caches the requested icon safely.
        :param url: The url of the icon.
        :return: The cached icon url.
        """
        self._logger.debug("IconManager request", url=url)
        try:
            return self._get(url)
        except Exception as e:
            self._logger.info("IconManager failed to get icon, defaulting..", e=e)
            return url

    def _get(self, url: str) -> str:
        """
        Gets and caches the requested icon.
        :param url: The url of the icon.
        :return: The cached icon url.
        """
        url = self._get_favicon_path(url, requests.get(url, headers={'User-Agent': self._user_agent})) or f'{url}/favicon.ico'
        self._logger.debug('IconManager favicon url', url=url)

        response = requests.get(url, headers={'User-Agent': self._user_agent})
        if response.status_code == 200:
            ico_hash = hashlib.sha256(response.content).hexdigest()
            self._logger.debug("IconManager favicon hash", icon_hash=ico_hash)

            ico = self._hashes.get(ico_hash, None)
            if not ico and self._imgur_client:
                ico = self._cache_icon(ico_hash, response.content)

            if ico:
                url = ico
                self._logger.debug("IconManager cached url", url=url)

        return url

    def save(self, target: str):
        """
        Saves the cache to a disk file.
        :param target: The target file.
        """
        with open(target, 'w+') as out:
            yaml.dump(self._hashes, out)

    def _cache_icon(self, ico_hash: str, content: bytes) -> Optional[str]:
        """
        Caches the icon and uploads it to our cache host.
        :param ico_hash: The icon hash from the original .ico file.
        :param content: The content bytes of the original .ico file.
        :return: The icon url from the cache host.
        """
        try:
            if self._imgur_client:
                temp_file_name = self._get_temp_file_name()
                Image.open(io.BytesIO(content)).save(temp_file_name, 'PNG')
                ico = self._imgur_client.upload_from_path(temp_file_name)['link']
                self._hashes[ico_hash] = ico
                return ico
        except OSError:
            # The website is supplying an invalid image :(
            pass

        return None

    @staticmethod
    def _get_favicon_path(url: str, response: requests.Response) -> Optional[str]:
        """
        Gets the custom favicon path, if available.
        :param response: The base url of the request.
        :param response: The response class from a request.
        :return: The url to the custom favicon or None if not available.
        """
        if response.status_code != 200:
            return None

        nodes = html.fromstring(response.content)
        icon = nodes.xpath('//link[contains(@rel, "icon") and contains(@href, "favicon")]')
        if len(icon) == 0:
            return None

        href = icon[-1].get('href')
        if href.startswith("http"):
            return href

        return urllib.parse.urljoin(url, href)

    @staticmethod
    def _get_temp_file_name() -> str:
        """
        Gets a temporary file name.
        :return: The temporary file name on the disk.
        """
        f = tempfile.NamedTemporaryFile()
        f.close()
        return f.name
