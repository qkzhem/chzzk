import re
import discord
from discord import app_commands
from discord.ext import commands

from views.stream_detail import StreamDetail

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class Broadcast(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="방송정보", description="스트리머의 방송 상태를 확인합니다.")
    @app_commands.describe(channel_id="스트리머의 채널 ID")
    async def _checkStream(self, interaction: discord.Interaction, channel_id: str) -> None:
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
                _streamer_info_data = await streamer_info.json()
                streamer_info_data = _streamer_info_data["content"]
                embed = discord.Embed(
                    title=streamer_info_data["channelName"], description=streamer_info_data["channelDescription"], color=0x00ff00)
                embed.set_footer(text=channel_id)
                embed.set_thumbnail(url=streamer_info_data["channelImageUrl"])
                embed.add_field(
                    name="방송 여부", value=f"{'방송중' if streamer_info_data['openLive'] else '방송중이 아님'}")
                if (streamer_info_data['openLive'] == True):
                    stream_info = await self.bot.http_client.get(
                        f"{BASE_URL}{channel_id}/live-detail")

                    if stream_info.status != 200:
                        embed.add_field(
                            name="방송 세부정보", value="방송 세부정보를 불러올 수 없습니다.")
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    stream_info = stream_info.json()["content"]
                    embed.set_image(url=stream_info["liveImageUrl"])
                    embed.add_field(
                        name="방송 제목", value=stream_info["liveTitle"], inline=False)
                    embed.add_field(
                        name="시작 시간", value=stream_info["openDate"], inline=False)

                    await interaction.response.send_message(embed=embed, ephemeral=True, view=StreamDetail())
                    await StreamDetail().wait()
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)

            else:
                await interaction.response.send_message("오류가 발생 하였습니다.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Broadcast(bot))