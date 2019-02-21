# DiscordNews
DiscordNews is a Discord bot that supplies daily news.

Current supported news sources:
* CodeProject

## Quick setup
First install the project requirements
```shell
$ python -m pip install -r requirements.txt
```
Afterwards, configure the file in `config/config.yaml` to your taste
```plaintext
servers: The list of servers the bot should post in
channel: The target channel where the news should be posted in
probe_news_delay: How much time(in seconds) to wait between checks
user_agent: The user agent to used when visting URLs
last_post_timestamp: The last post timestamp
```
And finally, run the script
```shell
$ cd <project_root>
$ python ./ --token <discord_token> --imgur <client_id>
            --config <config_path> --icons <cache_path>
```

The imgur client-id is used for icon caching, not every website is allowing Discord to access their favicon so we just push it once to imgur and use it's hash for re-usage. This is not mandatory and can be omitted.

## Imgur
To use this caching, you'll need to provide the script with a client-id which enables the usage of Imgur API, to do this you'll need to register your application with their service.
The script uses anonymous uploading and so requires only the client-id without a secret.

Head over to https://api.imgur.com/oauth2/addclient to register.