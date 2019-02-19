import argparse
import yaml
import imgurpython
import signal
import sys
from bot import Bot
from icon_manager import IconManager
from logger import Logger


def get_args():
    """
    Gets and parses the arguments for the bot.
    :return: The parsed arguments.
    """
    args = argparse.ArgumentParser(prog="NewsBot")
    args.add_argument('--token', help='The bot token to be used to authenticate against discord')
    args.add_argument('--imgur', help='The imgur client id to be used for uploading the .ico')
    args.add_argument('--config', help='The config file that contains most of the settings')
    args.add_argument('--icons', help='The icons cache file')
    args.add_argument('--debug', help='Sets the logger to output debug into console',
                      required=False, action='store_true')
    return args.parse_args()


def load_yaml(file_path):
    """
    Loads the YAML file.
    :param file_path: The file path of the YAML file.
    :return: The parsed YAML data, or None if the loading fails.
    """
    try:
        with open(file_path, 'r') as config_file:
            return yaml.load(config_file.read())
    except yaml.parser.ParserError:
        return None
    except FileNotFoundError:
        return None


def save_and_close(args, icon_mgr, bot):
    """
    Saves all of the configurations and exits.
    :param args: The arguments which the application loaded with.
    :param icon_mgr: The icon manager instance to save.
    :param bot: The bot instance to save.
    """
    Logger.get_logger().info("Saving and closing..")
    icon_mgr.save(args.icons)
    bot.save(args.config)
    sys.exit(0)


def main():
    args = get_args()
    config = load_yaml(args.config)
    if config is None:
        return 1

    Logger.IS_DEBUG = args.debug

    try:
        imgur_client = imgurpython.ImgurClient(args.imgur, None)
    except imgurpython.helpers.error.ImgurClientError:
        imgur_client = None
    icon_mgr = IconManager(imgur_client, load_yaml(args.icons), config["user_agent"])
    bot = Bot(args.token, config, icon_mgr)

    signal.signal(signal.SIGINT, lambda s, f: save_and_close(args, icon_mgr, bot))
    bot.run()


if __name__ == '__main__':
    main()
