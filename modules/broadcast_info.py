import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from views.stream_detail import StreamDetail

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class BroadcastInfo(commands.Cog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    async def cog_unload(self) -> None:
        await self.session.close()
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
            print(f"Error fetching stream info: {e}")
            return None
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error fetching stream info: {e}")
            return None

    @app_commands.command(name="방송정보", description="스트리머의 방송 상태를 확인합니다.")
    @app_commands.describe(channel_id="스트리머의 채널 ID")
    async def _stream_info(self, interaction: discord.Interaction, channel_id: str) -> None:
        streamer_info_data = await self.fetch_streamer_info(channel_id)

        if not streamer_info_data or streamer_info_data["code"] != 200:
            await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
            return

        streamer_info_data = streamer_info_data["content"]
        if streamer_info_data["channelId"] is None:
            await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)
            return

        embed = discord.Embed(
            title=streamer_info_data["channelName"], description=streamer_info_data["channelDescription"], color=0x00ff00)
        embed.set_footer(text=channel_id)
        embed.set_thumbnail(
            url=streamer_info_data["channelImageUrl"])
        embed.add_field(
            name="방송 여부", value=f"{'방송중' if streamer_info_data['openLive'] else '방송중이 아님'}")

        if streamer_info_data['openLive']:
            stream_info_data = await self.fetch_stream_info(channel_id)

            if not stream_info_data or stream_info_data["code"] != 200:
                embed.add_field(
                    name="방송 세부정보", value="방송 세부정보를 불러올 수 없습니다.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            stream_info_data = stream_info_data["content"]
            embed.timestamp = discord.utils.utcnow()
            embed.set_image(
                url=stream_info_data["liveImageUrl"].replace("{type}", "720"))
            embed.add_field(
                name="방송 제목", value=stream_info_data["liveTitle"], inline=False)
            embed.add_field(
                name="시작 시간", value=stream_info_data["openDate"], inline=False)
            embed.add_field(
                name="현재 시청자 수", value=f"{stream_info_data['concurrentUserCount']}명", inline=False)
            embed.add_field(
                name="누적 시청자 수", value=f"{stream_info_data['accumulateCount']}명", inline=False)
            embed.add_field(
                name="카테고리", value=f"{'미정' if stream_info_data['liveCategoryValue'] == '' else stream_info_data['liveCategoryValue']}", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True, view=StreamDetail())
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    session = aiohttp.ClientSession()
    cog = BroadcastInfo(bot, session)
    await bot.add_cog(cog)
