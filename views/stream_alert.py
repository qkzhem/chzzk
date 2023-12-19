from asyncio import sleep
import discord
from db.index import DB

from models.guild import Guild

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class StreamAlertCreateConfirm(discord.ui.View):
    def __init__(self, timeout=15, **kwargs):
        self.interaction = kwargs["interaction"]
        self.channel_id = kwargs["channel_id"]
        self.alert_channel = kwargs["alert_channel"]
        self.alert_text = kwargs["alert_text"]
        super().__init__(timeout=timeout)

    @discord.ui.button(label="이대로 할레요", style=discord.ButtonStyle.success, custom_id="stream_alert_create_confirm")
    async def _alert_create_confirm(self, interaction: discord.Interaction, confirm_button: discord.ui.Button):
        data = interaction.data
        print(data)
        with DB().getSession() as session:
            statements = session.query(Guild).filter_by(
                guild_id=interaction.guild.id).first()
            if statements == None:
                statements = Guild(
                    guild_id=interaction.guild.id, streamer_id=self.channel_id, alert_channel=self.alert_channel.id, alert_text=self.alert_text, activated=True)
                session.add(statements)
                session.commit()
            else:
                statements.streamer_id = self.channel_id
                statements.alert_channel = self.alert_channel.id
                statements.alert_text = self.alert_text
                session.commit()
        await interaction.response.edit_message(content="방송 알림을 설정하였습니다.", view=None, embed=None, delete_after=5)
        self.value = True
        self.stop()

    @discord.ui.button(label="취소", style=discord.ButtonStyle.red, custom_id="stream_alert_cancel")
    async def _alert_create_cancel(self, interaction: discord.Interaction, cancel_button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.edit_message(content="취소되었습니다.", view=None, embed=None, delete_after=5)

    async def on_timeout(self) -> None:
        timeout_message = await self.interaction.followup.send(content="시간이 초과되었습니다.", ephemeral=True)
        await sleep(5)
        await timeout_message.delete()
        return await super().on_timeout()
