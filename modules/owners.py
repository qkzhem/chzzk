from pathlib import Path
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands


import SECRETS


class Owners(commands.Cog, name="관리자 전용"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.guild_only()
    @app_commands.command(name="sync", description="명령어를 동기화 합니다.")
    async def _sync(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in SECRETS.owners:
            return await interaction.response.send_message("당신은 봇의 소유자가 아닙니다.", ephemeral=True)
        ret = 0
        for guild in self.bot.guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await interaction.response.send_message(f"{ret}/{len(self.bot.guilds)} 서버에 동기화를 완료했습니다.", ephemeral=True)

    @app_commands.command(name="reload", description="모듈을 다시 로드합니다.")
    @app_commands.describe(module="대상 모듈")
    async def _reload(self, interaction: discord.Interaction, module: str = None) -> None:
        if interaction.user.id not in SECRETS.owners:
            return await interaction.response.send_message("당신은 봇의 소유자가 아닙니다.", ephemeral=True)
        commands = [x.stem for x in Path('modules').glob('*.py')]
        error = ""
        reloaded_module = ""
        failed_module = ""

        if module:
            if module not in commands:
                return await interaction.response.send_message(f"모듈 `{module}`을(를) 찾을 수 없습니다.", ephemeral=True)
            commands = [module]

        for extension in commands:
            try:
                await self.bot.reload_extension(f'modules.{extension}')
                print(f'{extension} 모듈 다시 로드됨.')
                reloaded_module += f'``{extension}``, '
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'모듈들을 다시 로드하는동안 오류가 발생하였습니다: {error}')
                reloaded_module += f'``{extension}``, '
                error += f'{error}\n'
            print('-' * 32)

        if failed_module == "":
            await interaction.response.send_message(f"다음 모듈(들)을 성공적으로 다시 로드 하였습니다: {reloaded_module[:-2]}", ephemeral=True)
        elif failed_module != "" and reloaded_module != "":
            await interaction.response.send_message(f"다음 모듈(들)을 성공적으로 다시 로드 하였습니다: {reloaded_module[:-2]}\n다음 모듈(들)을 다시 로드하는데 실패하였습니다: {failed_module[:-2]}\n오류 로그: ```python\n{error}```", ephemeral=True)
        else:
            await interaction.response.send_message(f"다음 모듈(들)을 다시 로드하는데 실패하였습니다: {failed_module[:-2]}\n오류 로그: ```python\n{error}````", ephemeral=True)

    @app_commands.command(name="load", description="모듈을 로드합니다.")
    @app_commands.describe(module="대상 모듈")
    async def _load(self, interaction: discord.Interaction, module: str) -> None:
        if interaction.user.id not in SECRETS.owners:
            return await interaction.response.send_message("당신은 봇의 소유자가 아닙니다.", ephemeral=True)
        commands = [x.stem for x in Path('modules').glob('*.py')]
        error = ""
        loaded_command = ""
        failed_module = ""

        if module not in commands:
            return await interaction.response.send_message(f"모듈 `{module}`을(를) 찾을 수 없습니다.", ephemeral=True)

        try:
            await self.bot.load_extension(f'modules.{module}')
            print(f'{module} 모듈 로드됨')
            loaded_command += f'``{module}``, '
        except Exception as e:
            error = f'{module}\n {type(e).__name__} : {e}'
            failed_module += f'``{module}``, '
            error += f'{error}\n'
            print(f'{failed_module} 모듈을 로드하는 동안 다음과 같은 오류가 발생하였습니다:\n{error}')

        if failed_module != "" and loaded_command == "":
            await interaction.response.send_message(f"다음 모듈(들)을 로드하는동안 오류가 발생하였습니다: {failed_module[:-2]}\n오류 로그: ```python\n{error}```", ephemeral=True)
        elif failed_module == "" and loaded_command != "":
            await interaction.response.send_message(f"다음 모듈(들)을 성공적으로 로드하였습니다: {loaded_command[:-2]}", ephemeral=True)
        else:
            await interaction.response.send_message(f"다음 모듈(들)을 성공적으로 로드하였습니다: {loaded_command[:-2]}\n다음 모듈(들)을 로드하는데 실패하였습니다: {failed_module[:-2]}\n오류 로그: ```python\n{error}```", ephemeral=True)

    @app_commands.command(name="unload", description="모듈을 언로드합니다.")
    @app_commands.describe(module="대상 모듈")
    async def _unload(self, interaction: discord.Interaction, module: str) -> None:
        if interaction.user.id not in SECRETS.owners:
            return await interaction.response.send_message("당신은 봇의 소유자가 아닙니다.", ephemeral=True)
        commands = [x.stem for x in Path('modules').glob('*.py')]
        error = ""
        loaded_command = ""
        failed_module = ""

        if module not in commands:
            return await interaction.response.send_message(f"모듈 `{module}`을(를) 찾을 수 없습니다.", ephemeral=True)

        if module == "owners":
            return await interaction.response.send_message("Owners 모듈은 언로드 할 수 없습니다.", ephemeral=True)

        try:
            await self.bot.unload_extension(f'modules.{module}')
            print(f'{module} 모듈을 언로드 하였습니다.')
            loaded_command += f'``{module}``, '
        except Exception as e:
            error = f'{module}\n {type(e).__name__} : {e}'
            failed_module += f'``{module}``, '
            error += f'{error}\n'
            print(f'{failed_module} 모듈을 언로드 하는 동안 다음과 같은 오류가 발생하였습니다:\n{error}')

        if failed_module != "" and loaded_command == "":
            await interaction.response.send_message(f"다음 모듈을 언로드 하는데 실패했습니다: {failed_module[:-2]}\n오류 로그: ```python\n{error}```", ephemeral=True)
        elif failed_module == "" and loaded_command != "":
            await interaction.response.send_message(f"다음 모듈을 성공적으로 언로드 하였습니다: {loaded_command[:-2]}", ephemeral=True)
        else:
            await interaction.response.send_message(f"성공적으로 언로드된 모듈(들): {loaded_command[:-2]}\n언로드 실패한 모듈(들): {failed_module[:-2]}\n오류 로그: ```python\n{error}```", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Owners(bot))
