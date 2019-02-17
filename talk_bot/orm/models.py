import peewee

db = peewee.SqliteDatabase('db.sqlite3')


class Message(peewee.Model):
    content = peewee.CharField()
    author_name = peewee.CharField()
    author_id = peewee.BigIntegerField()
    timestamp = peewee.DateField()

    class Meta:
        database = db


class IgnoredChannel(peewee.Model):
    channel_id = peewee.BigIntegerField()

    class Meta:
        database = db
