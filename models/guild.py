from main import DB_instance
from sqlalchemy import Column, Integer, String, Text


class Guild(DB_instance):
    __tablename__ = "guilds"
    guild_id = Column(Text, primary_key=True)
    target_channel = Column(Text)
    alert_text = Column(Text)

    def __init__(self, guild_id, target_channel, alert_text):
        self.guild_id = guild_id
        self.target_channel = target_channel
        self.alert_text = alert_text
