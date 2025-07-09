# bot/cogs/management.py
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio

from core.config import config
from core.errors import GameServerError
from services.game_server import GameServer
from services.server_manager import server_manager

log = logging.getLogger(__name__)

def get_server_choices():
    return [
        app_commands.Choice(name=server.name, value=server_id)
        for server_id, server in config.servers.items()
    ]

class ManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def notify_status_change(self, server_instance: 'GameServer', online: bool):
        """Envia uma notificação para o canal apropriado sobre a mudança de status."""
        channel_id = config.bot.notification_channel_id
        channel = self.bot.get_channel(channel_id)
        if not channel:
            log.warning(f"Canal de notificação com ID {channel_id} não encontrado.")
            return

        role_id = server_instance.config.mention_role_id
        role = channel.guild.get_role(role_id)
        
        if online:
            embed = discord.Embed(
                title=f"✅ Servidor Online: {server_instance.config.name}",
                description="O servidor já está disponível para conexão!",
                color=discord.Color.green()
            )
            content = role.mention if role else ""
            await channel.send(content=content, embed=embed)
        else:
            embed = discord.Embed(
                title=f"❌ Servidor Offline: {server_instance.config.name}",
                description="O servidor foi desligado.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

    @app_commands.command(name="start", description="Inicia um servidor de jogo.")
    @app_commands.choices(game=get_server_choices())
    @app_commands.checks.has_role(config.bot.authorized_role_id)
    async def start(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        server_instance = server_manager.get_server(game.value)
        
        # A lógica volta a ser simples, pois is_running() é confiável
        if server_instance.is_running():
            await interaction.followup.send(f"⚠️ O servidor **{server_instance.config.name}** já está em execução!", ephemeral=True)
            return

        try:
            message = await server_instance.start()
            await interaction.followup.send(message)
            
            # Pausa para dar tempo ao servidor de iniciar antes de notificar
            await asyncio.sleep(15) 
            if server_instance.is_running():
                await self.notify_status_change(server_instance, online=True)
        except GameServerError as e:
            await interaction.followup.send(f"❌ {e}", ephemeral=True)

    @app_commands.command(name="stop", description="Para um servidor de jogo.")
    @app_commands.choices(game=get_server_choices())
    @app_commands.checks.has_role(config.bot.authorized_role_id)
    async def stop(self, interaction: discord.Interaction, game: app_commands.Choice[str], force: bool = False):
        await interaction.response.defer(ephemeral=True)
        server_instance = server_manager.get_server(game.value)
        
        # A verificação síncrona e simples volta a funcionar
        if not server_instance.is_running():
            await interaction.followup.send(f"O servidor **{server_instance.config.name}** não está em execução.")
            return

        was_running = server_instance.is_running()
        message = await server_instance.stop(force=force)
        await interaction.followup.send(message)
        
        # Pausa para o servidor desligar
        await asyncio.sleep(5)
        if was_running and not server_instance.is_running():
            await self.notify_status_change(server_instance, online=False)

    @app_commands.command(name="status", description="Verifica o status dos servidores.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        embed = discord.Embed(title="Status dos Servidores", color=discord.Color.gold())
        running_servers = server_manager.get_all_running_servers()

        if not running_servers:
            embed.description = "Nenhum servidor está online no momento."
            await interaction.followup.send(embed=embed)
            return
        
        # A lógica do status volta a ser simples e confiável
        for server in running_servers:
            status_message = await server.get_status()
            embed.add_field(name=f"**{server.config.name}**", value=status_message, inline=False)
        
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    guild = discord.Object(id=config.bot.guild_id)
    await bot.add_cog(ManagementCog(bot), guilds=[guild])