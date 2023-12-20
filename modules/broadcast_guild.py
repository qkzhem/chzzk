import typing
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from db.index import DB
from models.guild import Guild
from views.stream_alert import StreamAlertCreateConfirm

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class BroadcastGuildAlert(commands.GroupCog, name="방송알림"):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession) -> None:
        self.bot = bot
        self.session = session
        self.alert_job.start()

    async def cog_unload(self) -> None:
        self.alert_job.cancel()
        return await super().cog_unload()

    async def fetch_streamer_info(self, channel_id: str):
        try:
            async with self.session.get(f"{BASE_URL}{channel_id}") as streamer_info:
                streamer_info.raise_for_status()
                return await streamer_info.json()
        except aiohttp.ClientResponseError as e:
            # Handle specific HTTP response errors
            print(f"Error fetching streamer info: {e}")
            return None
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error fetching streamer info: {e}")
            return None

    async def fetch_stream_info(self, channel_id: str):
        try:
            async with self.session.get(f"{BASE_URL}{channel_id}/live-detail") as streamer_info:
                streamer_info.raise_for_status()
                return await streamer_info.json()
        except aiohttp.ClientResponseError as e:
            # Handle specific HTTP response errors
            print(f"Error fetching streamer info: {e}")
            return None
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error fetching streamer info: {e}")
            return None

    @tasks.loop(minutes=5)
    async def alert_job(self):
        try:
            with DB().getSession() as session:
                statements = session.query(
                    Guild).filter_by(activated=True).all()
                for statement in statements:
                    streamer_info = await self.fetch_streamer_info(statement.streamer_id)
                    streamer_info = streamer_info["content"]

                    if streamer_info["channelId"] is None:
                        continue

                    stream_info_data = await self.fetch_stream_info(statement.streamer_id)
                    stream_info_data = stream_info_data["content"]

                    if streamer_info["openLive"]:
                        if statement.is_streaming == True:
                            continue
                        else:
                            statement.is_streaming = True
                            session.commit()
                            embed = discord.Embed(
                                title=streamer_info["channelName"], description=streamer_info["channelDescription"], color=0x00ff00)
                            embed.set_footer(text=statement.streamer_id)
                            embed.timestamp = discord.utils.utcnow()
                            embed.set_image(
                                url=stream_info_data["liveImageUrl"].replace("{type}", "720"))
                            embed.set_thumbnail(
                                url=streamer_info["channelImageUrl"])
                            embed.add_field(
                                name="시청자 수", value=f"{stream_info_data['concurrentUserCount']}명")
                            embed.add_field(
                                name="카테고리", value=f"{'미정' if stream_info_data['liveCategoryValue'] == '' else stream_info_data['liveCategoryValue']}")
                            channel = await self.bot.fetch_channel(statement.alert_channel)
                            await channel.send(content=statement.alert_text, embed=embed)
                            continue
                    else:
                        if statement.is_streaming == False:
                            continue
                        else:
                            statement.is_streaming = False
                            session.commit()
                            continue
        except Exception as e:
            print(e.with_traceback())
            pass

    @app_commands.command(name="설정", description="방송 알림을 설정합니다.")
    @app_commands.describe(channel_id="스트리머의 채널 ID", alert_channel="알림을 받을 채널", alert_text="알림과 함께 전송될 메세지")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def _set_stream_alert(self, interaction: discord.Interaction,
                                channel_id: str, alert_channel: discord.TextChannel,
                                alert_text: typing.Optional[str]) -> None:
        streamer_info = await self.fetch_streamer_info(channel_id)

        if not streamer_info or streamer_info["code"] != 200:
            await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
            return

        streamer_info = streamer_info["content"]
        if streamer_info["channelId"] is None:
            await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
            return

        stream_info_data = await self.fetch_stream_info(channel_id)
        if not stream_info_data or stream_info_data["code"] != 200:
            await interaction.response.send_message("치지직 서버 오류입니다.", ephemeral=True)
            return

        stream_info_data = stream_info_data["content"]

        embed = discord.Embed(
            title=streamer_info["channelName"], description=streamer_info["channelDescription"], color=0x00ff00)
        embed.set_footer(text=channel_id)
        embed.timestamp = discord.utils.utcnow()
        embed.set_image(
            url=stream_info_data["liveImageUrl"].replace("{type}", "720"))
        embed.set_thumbnail(url=streamer_info["channelImageUrl"])
        embed.add_field(
            name="시청자 수", value=f"{stream_info_data['concurrentUserCount']}명")
        embed.add_field(
            name="카테고리", value=f"{'미정' if stream_info_data['liveCategoryValue'] == '' else stream_info_data['liveCategoryValue']}")

        view = StreamAlertCreateConfirm(timeout=10, interaction=interaction,
                                        channel_id=channel_id, alert_channel=alert_channel, alert_text=alert_text)

        await interaction.response.send_message(content=f"방송 시작이 감지되면 아래와 같이 메세지가 발송됩니다.\n\n{alert_text if alert_text else ''}", embed=embed, ephemeral=True, view=view, delete_after=15)

    @app_commands.command(name="끄기", description="방송 알림을 비활성화합니다.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def _alert_disable(self, interaction: discord.Interaction) -> None:
        with DB().getSession() as session:
            statements = session.query(
                Guild).filter_by(guild_id=interaction.guild.id).first()
            if statements == None:
                await interaction.response.send_message("방송 알림이 설정되어있지 않습니다.", ephemeral=True)
                return
            else:
                statements.activated = False
                session.commit()
                await interaction.response.send_message("방송 알림을 비활성화하였습니다.", ephemeral=True)
                return

    @app_commands.command(name="켜기", description="방송 알림을 활성화합니다.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def _alert_enable(self, interaction: discord.Interaction) -> None:
        with DB().getSession() as session:
            statements = session.query(
                Guild).filter_by(guild_id=interaction.guild.id).first()
            if statements == None:
                await interaction.response.send_message("방송 알림이 설정되어있지 않습니다.", ephemeral=True)
                return
            else:
                statements.activated = True
                session.commit()
                await interaction.response.send_message("방송 알림을 활성화하였습니다.", ephemeral=True)
                return

    @app_commands.command(name="정보", description="방송 알림 정보를 출력합니다.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def _alert_info(self, interaction: discord.Interaction) -> None:
        with DB().getSession() as session:
            statements = session.query(
                Guild).filter_by(guild_id=interaction.guild.id).first()
            if statements == None:
                await interaction.response.send_message("방송 알림이 설정되어있지 않습니다.", ephemeral=True)
                return
            else:
                streamer_info = await self.fetch_streamer_info(statements.streamer_id)
                streamer_info = streamer_info["content"]

                if streamer_info["channelId"] is None:
                    await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
                    return

                stream_info_data = await self.fetch_stream_info(statements.streamer_id)
                stream_info_data = stream_info_data["content"]

                embed = discord.Embed(
                    title=streamer_info["channelName"], description=streamer_info["channelDescription"], color=0x00ff00)
                embed.set_footer(text=statements.streamer_id)
                embed.timestamp = discord.utils.utcnow()
                embed.set_image(
                    url=stream_info_data["liveImageUrl"].replace("{type}", "720"))
                embed.set_thumbnail(url=streamer_info["channelImageUrl"])
                embed.add_field(
                    name="시청자 수", value=f"{stream_info_data['concurrentUserCount']}명")
                embed.add_field(
                    name="카테고리", value=f"{'미정' if stream_info_data['liveCategoryValue'] == '' else stream_info_data['liveCategoryValue']}")

                await interaction.response.send_message(content=f"방송 시작이 감지되면 아래와 같이 메세지가 발송됩니다.\n\n{statements.alert_text if statements.alert_text else ''}", embed=embed, ephemeral=True, delete_after=15)
                return

    @_set_stream_alert.error
    async def _set_stream_alert_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        print(error)
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="이 명령어를 실행할 권한이 없는 것 같습니다.", ephemeral=True)

    @_alert_disable.error
    async def _alert_disable_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="이 명령어를 실행할 권한이 없는 것 같습니다.", ephemeral=True)

    @_alert_enable.error
    async def _alert_enable_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="이 명령어를 실행할 권한이 없는 것 같습니다.", ephemeral=True)

    @_alert_info.error
    async def _alert_info_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(content="이 명령어를 실행할 권한이 없는 것 같습니다.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    session = aiohttp.ClientSession()
    cog = BroadcastGuildAlert(bot, session)
    await bot.add_cog(cog)
