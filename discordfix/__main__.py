import sys
import os.path

from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location


class DiscordFixPathFinder(MetaPathFinder):
    @staticmethod
    def find_spec(fullname, *_):
        if fullname == 'discord.compat':
            filename = os.path.join(os.getcwd(), 'discordfix', 'compat.py')
            return spec_from_file_location(fullname, filename, loader=DiscordFixLoader(filename),
                                           submodule_search_locations=[])
        return None


class DiscordFixLoader(Loader):
    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.filename) as f:
            data = f.read()
        exec(data, vars(module))

    def module_repr(self, module):
        super().module_repr(module)


def install():
    """
    Installs the discord.py fix for python3.7
    """
    sys.meta_path.insert(0, DiscordFixPathFinder())


if __name__ == 'discordfix.__main__':
    # Once imported, install the fix so we could import everything else normally.
    install()
