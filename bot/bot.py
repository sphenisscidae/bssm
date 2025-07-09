# bot/bot.py
import discord
from discord.ext import commands
import asyncio
import logging
import logging.handlers

from core.config import config, secrets
from core.errors import GameServerError

def setup_logging():
    """Configura o sistema de logging."""
    log = logging.getLogger()
    log.setLevel(logging.INFO)

    # Handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s'))
    
    # Handler para arquivo (rotaciona o arquivo para não ficar gigante)
    file_handler = logging.handlers.RotatingFileHandler(
        filename='discord_bot.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s'))
    
    log.addHandler(console_handler)
    log.addHandler(file_handler)

setup_logging()
log = logging.getLogger(__name__)

class GameServerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        log.info("Carregando extensões (Cogs)...")
        await self.load_extension("bot.cogs.management")
        log.info("Sincronizando comandos com o Discord. Isso pode levar um minuto...")
        await self.tree.sync(guild=discord.Object(id=config.bot.guild_id))
        log.info("Sincronização concluída.")

    async def on_ready(self):
        log.info(f'Bot conectado como {self.user} (ID: {self.user.id})')

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handler global para erros em comandos."""
        original_error = getattr(error, 'original', error)
        
        if isinstance(original_error, discord.app_commands.CheckFailure):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        if isinstance(original_error, GameServerError):
            await interaction.response.send_message(f"❌ {original_error}", ephemeral=True)
            log.warning(f"Erro de negócio tratado para o usuário {interaction.user}: {original_error}")
            return

        # Para todos os outros erros, logamos o traceback completo
        log.exception(f"Erro inesperado no comando /{interaction.command.name}", exc_info=original_error)

        user_message = "Ocorreu um erro inesperado. A equipe de administração foi notificada."
        if not interaction.response.is_done():
            await interaction.response.send_message(user_message, ephemeral=True)
        else:
            await interaction.followup.send(user_message, ephemeral=True)
        
        admin_channel = self.get_channel(config.bot.admin_notification_channel_id)
        if admin_channel:
            embed = discord.Embed(
                title="🚨 Erro Crítico no Bot",
                description=f"Comando: `/{interaction.command.name}`\nUsuário: {interaction.user.mention}",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Erro", value=f"```{type(original_error).__name__}: {original_error}```")
            await admin_channel.send(embed=embed)

async def main():
    bot = GameServerBot()
    await bot.start(secrets.discord_bot_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot desligado pelo usuário.")