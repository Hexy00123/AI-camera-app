from peewee import *

db = SqliteDatabase('Settings.db')


class BaseModel(Model):
    class Meta:
        database = db


class SettingsData(BaseModel):
    name = TextField()
    wb = BooleanField()
    invert = BooleanField()
    flip_v = BooleanField()
    flip_g = BooleanField()
    face = BooleanField()
    brightnes = IntegerField()
    contrast = IntegerField()


class WaysData(BaseModel):
    way = TextField()
    name = TextField()
    additional = IntegerField()



