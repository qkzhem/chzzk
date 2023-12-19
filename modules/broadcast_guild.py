import typing
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from db.index import DB
from models.guild import Guild
from views.stream_alert import StreamAlertCreateConfirm

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class BroadcastGuildAlert(commands.GroupCog, name="방송알림"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.alert_job.start()

    def cog_unload(self) -> None:
        self.alert_job.cancel()

    @tasks.loop(seconds=10)
    async def alert_job(self):
        with DB().getSession() as session:
            statements = session.query(Guild).filter_by(activated=True).all()
            for statement in statements:
                async with self.bot.http_client.get(f"{BASE_URL}{statement.streamer_id}") as streamer_info:
                    if streamer_info.status != 200:
                        continue
                    _streamer_info = await streamer_info.json()
                    streamer_info = _streamer_info["content"]
                    if streamer_info["openLive"] == True:
                        if statement.alert_text == None:
                            channel = await self.bot.fetch_channel(
                                statement.alert_channel)
                            await channel.send(content=f"{streamer_info['channelName']}님이 방송을 시작하였습니다.")
                        else:
                            await self.bot.get_guild(statement.guild_id).get_channel(statement.alert_channel).send(content=f"{streamer_info['channelName']}님이 방송을 시작하였습니다.\n{statement.alert_text}")
                    else:
                        continue

    @app_commands.command(name="설정", description="방송 알림을 설정합니다.")
    @app_commands.describe(channel_id="스트리머의 채널 ID", alert_channel="알림을 받을 채널", alert_text="알림과 함께 전송될 메세지")
    async def _check_stream(self, interaction: discord.Interaction,
                            channel_id: str, alert_channel: discord.TextChannel,
                            alert_text: typing.Optional[str]) -> None:

        async with self.bot.http_client.get(
                f"{BASE_URL}{channel_id}") as streamer_info:

            if streamer_info.status == 404:
                await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
                return
            elif streamer_info.status == 403:
                await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
                return
            elif streamer_info.status == 500:
                await interaction.response.send_message("치지직 서버 오류입니다.", ephemeral=True)
                return
            elif streamer_info.status == 200:
                _streamer_info = await streamer_info.json()
                streamer_info = _streamer_info["content"]
                if streamer_info["channelId"] == None:
                    await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
                    return
                _stream_info_data = await self.bot.http_client.get(
                    f"{BASE_URL}{channel_id}/live-detail")
                stream_info_data = await _stream_info_data.json()

                embed = discord.Embed(
                    title=streamer_info["channelName"], description=streamer_info["channelDescription"], color=0x00ff00)
                embed.set_footer(text=channel_id)
                embed.timestamp = discord.utils.utcnow()
                embed.set_image(
                    url=stream_info_data["content"]["liveImageUrl"].replace("{type}", "720"))
                embed.set_thumbnail(url=streamer_info["channelImageUrl"])
                embed.add_field(
                    name="시청자 수", value=f"{stream_info_data['content']['concurrentUserCount']}명")
                embed.add_field(
                    name="카테고리", value=f"{'미정' if stream_info_data['content']['liveCategoryValue'] == '' else stream_info_data['content']['liveCategoryValue']}")
                view = StreamAlertCreateConfirm(timeout=10, interaction=interaction,
                                                channel_id=channel_id, alert_channel=alert_channel, alert_text=alert_text)

                await interaction.response.send_message(content=f"방송 시작이 감지되면 아래와 같이 메세지가 발송됩니다.\n\n{alert_text if alert_text != None else ''}", embed=embed, ephemeral=True, view=view, delete_after=15)
            else:
                await interaction.response.send_message(f"오류가 발생 하였습니다.\n오류 코드: {streamer_info.status}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BroadcastGuildAlert(bot))
