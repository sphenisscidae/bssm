# services/minecraft_server.py
import subprocess
from aiomcrcon import Client, RCONConnectionError
from .game_server import GameServer
from core.errors import ServerStartError, RconConnectionError as CustomRconError

class MinecraftServer(GameServer):
    """Implementação de GameServer para servidores Minecraft."""

    async def start(self) -> str:
        if self.is_running():
            raise ServerStartError(f"O servidor **{self.config.name}** já parece estar em execução!")

        try:
            self.process = subprocess.Popen(
                self.config.start_command,
                cwd=self.config.path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return f"O servidor **{self.config.name}** foi iniciado com sucesso!"
        except (FileNotFoundError, OSError) as e:
            raise ServerStartError(f"Falha ao iniciar o processo do Minecraft: Verifique o 'path' e o comando 'java'. Erro: {e}")

    async def stop(self, force: bool = False) -> str:
        if not self.is_running():
            return f"O servidor **{self.config.name}** não está em execução."

        if force:
            self.process.kill()
            await self.process.wait()
            return f"O servidor **{self.config.name}** foi forçadamente encerrado."

        try:
            async with Client(self.config.rcon.host, self.config.rcon.port, self.config.rcon.password) as client:
                await client.send_cmd("stop")
            
            self.process.wait(timeout=60)
            return f"O servidor **{self.config.name}** foi parado com sucesso."
        except RCONConnectionError:
            self.process.kill()
            raise CustomRconError("Não foi possível conectar via RCON para parar. O processo foi encerrado à força.")
        except subprocess.TimeoutExpired:
            self.process.kill()
            return f"O servidor **{self.config.name}** demorou a responder e foi forçado a fechar."

    async def get_status(self) -> str:
        try:
            async with Client(self.config.rcon.host, self.config.rcon.port, self.config.rcon.password) as client:
                list_resp, _ = await client.send_cmd("list")
            
            parts = list_resp.split()
            player_count = f"{parts[2]}/{parts[7]}"
            players = " ".join(parts[10:]) if len(parts) > 10 else "Nenhum"
            return f"🟢 **Online** | Jogadores: **{player_count}**\n`{players}`"
        except RCONConnectionError:
            return "🟡 **Online** (Falha na conexão RCON)"
        except Exception:
            return "🟡 **Online** (RCON respondeu de forma inesperada)"