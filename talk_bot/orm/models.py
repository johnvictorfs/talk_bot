import json

import peewee
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, 'orm', 'db_credentials.json'), 'r') as f:
    credentials = json.load(f)

db = peewee.PostgresqlDatabase(
    credentials['name'],
    user=credentials['user'],
    password=credentials['password'],
    host=credentials['host'],
    port=credentials['port']
)


class Message(peewee.Model):
    content = peewee.CharField()
    author_name = peewee.CharField()
    author_id = peewee.BigIntegerField()
    channel_id = peewee.BigIntegerField(null=True)
    timestamp = peewee.DateTimeField(null=True)

    class Meta:
        database = db


class IgnoredChannel(peewee.Model):
    channel_id = peewee.BigIntegerField()

    class Meta:
        database = db
