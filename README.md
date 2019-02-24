# Talk-bot

#### A discord bot that uses Markov chains to generate new messages from the ones the bot reads and sents them in another channel. Made in Python using the [discord.py](https://github.com/Rapptz/discord.py/tree/rewrite) library.

***

The bot stores all messages from discord channels that he can reach (new or old) in a Postgres Database that were not sent by a Bot or in a NSFW channel (and some other formatting rules). 

From those messages it then makes up new messages using a markov chain logic and sends them back in a configured channel in `talk_bot/settings.json` every 5 minutes (by default, can be changed in the settings as well). 

The bot could easily be changed to make use of a more robust message history and data to create better messages (perhaps with the use of Machine Learning). The code for creating and sending the messages is present at [`talk_bot/tasks/sender.py`](talk_bot/tasks/sender.py).

***

#### Setup

- The bot requires Python 3.6 or higher to run

- Dependencies are present in the `pyproject.toml` file and can be easily installed with [`poetry`](https://github.com/sdispater/poetry) with `$ poetry install`

- Rename [`talk_bot/orm/db_credentials.example.json`](talk_bot/orm/db_credentials.example.json) to `db_credentials.json` and put in the database credentials for a Postgres database
    - Or, if you wish to use a Sqlite database, uncomment the `db = peewee.SqliteDatabase('bot.db')` line at [`talk_bot/orm/models.py`](talk_bot/orm/models.py)

- Rename [`talk_bot/settings.example.json`](talk_bot/settings.example.json) to `settings.json` and edit in the needed fields

    - You can create a discord bot and get its token at https://discordapp.com/developers/applications/  (Do not share your token with anyone!)
    - `messages_channel` needs to be the ID of the channel you want the bot to send the generated messages to, you can get the ID of a channel in Discord by turning on the Developer Mode in the settings, and right-clicking a channel and pressing 'Copy ID'
    - `messages_delay` is the delay (in minutes) between messages the bot sends to the configured channel

***

#### Running

- `$ cd talk_bot`
- `$ python bot.py`

***

#### Discord Commands

- `!ignore <channel>` Messages from ignored channels are not added to the database (not retro-active)
    - Requires the `Manage Channels` permission
- `!ignore <channel>` Un-ignores a channel
    - Requires the `Manage channels` permission
- `!clean_db` Deletes any messages already in the bot's database that don't meet the necessary criteria to be there, also deletes messages that were sent in a channel that is now ignored
    - Can only be used by the bot's instance Owner