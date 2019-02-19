import requests
import hashlib
import tempfile
import io
import json
import urllib.parse
from PIL import Image
from logger import Logger
from lxml import html


class IconManager:
    def __init__(self, imgur, data, user_agent):
        self._imgur_client = imgur
        self._hashes = data
        self._user_agent = user_agent
        self._logger = Logger.get_logger()

    def get(self, url):
        """
        Gets and caches the requested icon.
        :param url: The url of the icon.
        :return: The cached icon url.
        """
        url = self._get_favicon_path(url, requests.get(url, {'User-Agent': self._user_agent})) or f'{url}/favicon.ico'
        self._logger.debug('IconManager favicon url', url=url)

        response = requests.get(url, {'User-Agent': self._user_agent})
        if response.status_code != 200:
            return None

        ico_hash = hashlib.sha256(response.content).hexdigest()
        self._logger.debug("IconManager favicon hash", icon_hash=ico_hash)

        ico = self._hashes.get(ico_hash, None)
        if not ico:
            ico = self._cache_icon(ico_hash, response.content)

        return ico

    def save(self, target):
        """
        Saves the cache to a disk file.
        :param target: The target file.
        """
        with open(target, 'w+') as out:
            json.dump(self._hashes, out)

    def _cache_icon(self, ico_hash, content):
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
    def _get_favicon_path(url, response):
        """
        Gets the custom favicon path, if available.
        :param response: The base url of the request.
        :param response: The response class from a request.
        :return: The url to the custom favicon or None if not available.
        """
        if response.status_code != 200:
            return None

        nodes = html.fromstring(response.content)
        icon = nodes.xpath('//link[@rel="shortcut icon"]')
        if not icon:
            return None

        href = icon[0].get('href')
        if href.startswith("http"):
            return href

        return urllib.parse.urljoin(url, href)

    @staticmethod
    def _get_temp_file_name():
        """
        Gets a temporary file name.
        :return: The temporary file name on the disk.
        """
        f = tempfile.NamedTemporaryFile()
        f.close()
        return f.name
