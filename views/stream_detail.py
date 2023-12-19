import aiohttp
import discord
import json

BASE_URL = "https://api.chzzk.naver.com/service/v1/channels/"


class StreamDetail(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)

    @discord.ui.button(label="방송 세부정보 확인", style=discord.ButtonStyle.gray)
    async def _check_stream_detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        async with aiohttp.ClientSession().get(
                f"{BASE_URL}{embed.footer.text}/live-detail") as stream_info_for_nerds:
            _stream_info_for_nerds = await stream_info_for_nerds.json()

            stream_info_for_nerds = json.loads(
                _stream_info_for_nerds["content"]["livePlaybackJson"]
            )

            HLS_data = []
            LLHLS_data = []

            for key, value in stream_info_for_nerds.items():
                if key == "media":
                    for media in value:
                        if media["mediaId"] == "HLS":
                            for stream in media["encodingTrack"]:
                                if stream["encodingTrackId"] == "alow.stream":
                                    continue
                                HLS_data.append(stream)
                        elif media["mediaId"] == "LLHLS":
                            for stream in media["encodingTrack"]:
                                if stream["encodingTrackId"] == "alow.stream":
                                    continue
                                LLHLS_data.append(stream)

            HLS_sorted_data = sorted(
                HLS_data, key=lambda x: x.get('videoBitRate', 0))

            LLHLS_sorted_data = sorted(
                LLHLS_data, key=lambda x: x.get('videoBitRate', 0))

            embed.add_field(name="실시간 스트림(HLS) 정보", value="")
            for hls_stream in HLS_sorted_data:
                embed.add_field(name=f"{hls_stream['encodingTrackId']} 스트림",
                                value=f"오디오 비트레이트: `{hls_stream['audioBitRate'] * 0.001}kbps`\n비디오 비트레이트: `{hls_stream['videoBitRate'] * 0.001}kbps`\n비디오 코덱: `{hls_stream['videoCodec']}`\n비디오가 HDR 인가요?: `{'아니요' if hls_stream['videoDynamicRange'] == 'SDR' else '네'}`", inline=False)

            embed.add_field(name="** **", value="", inline=False)

            embed.add_field(name="저지연 실시간 스트림(LLHLS) 정보", value="")
            for llhls_stream in LLHLS_sorted_data:
                embed.add_field(name=f"{llhls_stream['encodingTrackId']} 스트림",
                                value=f"오디오 비트레이트: `{llhls_stream['audioBitRate'] * 0.001}kbps`\n비디오 비트레이트: `{hls_stream['videoBitRate'] * 0.001}kbps`\n비디오 코덱: `{hls_stream['videoCodec']}`\n비디오가 HDR 인가요?: `{'아니요' if hls_stream['videoDynamicRange'] == 'SDR' else '네'}`", inline=False)

            await interaction.response.edit_message(embed=embed, view=None)
            self.value = True
            self.stop()
