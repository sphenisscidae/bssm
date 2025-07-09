import subprocess
from .game_server import GameServer
from core.errors import ServerStartError
from aiomcrcon import Client, RCONConnectionError, IncorrectPasswordError

# SUBSTITUA A CLASSE INTEIRA PELA VERSÃO ABAIXO
class FactorioServer(GameServer):
    """Implementação de GameServer para servidores Factorio, com controle de processo robusto."""

    async def start(self) -> str:
        if self.is_running():
            raise ServerStartError(f"O servidor **{self.config.name}** já parece estar em execução!")

        try:
            # A MÁGICA FINAL ESTÁ AQUI: Usamos DETACHED_PROCESS
            # Isso cria um processo totalmente novo e independente, forçando a criação de uma nova janela de console.
            self.process = subprocess.Popen(
                self.config.start_command,
                cwd=self.config.path,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return f"O servidor **{self.config.name}** foi iniciado!"
        except (FileNotFoundError, OSError) as e:
            raise ServerStartError(f"Falha ao iniciar o processo do Factorio: Verifique o 'path' e o comando. Erro: {e}")

    def is_running(self) -> bool:
        """
        Com DETACHED_PROCESS, o self.process é confiável.
        Voltamos à verificação de processo simples e síncrona.
        """
        # Se não temos um processo, não está rodando.
        if not self.process:
            return False
        # poll() retorna None se o processo ainda está rodando.
        return self.process.poll() is None

    # O método stop continua o mesmo, pois o RCON é o caminho certo.
    async def stop(self, force: bool = False) -> str:
        if not self.is_running():
            return f"O servidor **{self.config.name}** não está em execução."

        # A lógica de 'force kill' agora volta a funcionar
        if force:
            self.process.kill()
            self.process = None # Limpamos o processo
            return f"O servidor **{self.config.name}** foi forçadamente encerrado."

        try:
            async with Client(self.config.rcon.host, self.config.rcon.port, self.config.rcon.password) as client:
                await client.send_cmd("/quit")
            return f"O servidor **{self.config.name}** foi instruído a parar."
        except (RCONConnectionError, IncorrectPasswordError) as e:
            raise ServerStartError(f"Falha ao conectar via RCON para parar o servidor. Talvez ele já tenha sido fechado? Erro: {e}")

    # O método get_status também continua o mesmo.
    async def get_status(self) -> str:
        try:
            async with Client(self.config.rcon.host, self.config.rcon.port, self.config.rcon.password) as client:
                players_resp, _ = await client.send_cmd("/players online")
            
            player_list = [line.strip() for line in players_resp.split('\n') if "online" not in line and line.strip()]
            player_count = len(player_list)
            player_names = ", ".join(player_list) if player_list else "Nenhum"
            return f"🟢 **Online** | Jogadores: **{player_count}**\n`{player_names}`"
        except Exception:
            # Se a verificação de status falhar, usamos nosso is_running() confiável para dar o status correto.
            if self.is_running():
                return "🟡 **Online** (RCON não está respondendo)"
            else:
                return "🔴 **Offline**"