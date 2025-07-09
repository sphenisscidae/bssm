# services/server_manager.py
from typing import Dict, Type
from core.config import config
from core.errors import ServerNotFoundError
from .game_server import GameServer
from .minecraft_server import MinecraftServer
from .factorio_server import FactorioServer

class ServerManager:
    """
    Gerencia o ciclo de vida e o estado dos servidores de jogos.
    Atua como uma Fábrica para criar a instância de servidor correta.
    """
    def __init__(self):
        self._server_factories: Dict[str, Type[GameServer]] = {
            "minecraft": MinecraftServer,
            "factorio": FactorioServer,
        }
        self._running_servers: Dict[str, GameServer] = {}

    def get_server(self, server_id: str) -> GameServer:
        """Obtém uma instância de servidor, criando uma nova se necessário."""
        if server_id in self._running_servers and self._running_servers[server_id].is_running():
            return self._running_servers[server_id]

        server_config = config.servers.get(server_id)
        if not server_config:
            raise ServerNotFoundError(f"Servidor '{server_id}' não encontrado na configuração.")

        factory = self._server_factories.get(server_config.game_type)
        if not factory:
            raise NotImplementedError(f"Tipo de jogo '{server_config.game_type}' não suportado.")

        instance = factory(server_id, server_config)
        self._running_servers[server_id] = instance
        return instance

    def get_all_running_servers(self) -> list[GameServer]:
        """Retorna uma lista de todas as instâncias de servidor ativas."""
        active_servers = []
        for server_id, server in list(self._running_servers.items()):
            if server.is_running():
                active_servers.append(server)
            else:
                del self._running_servers[server_id]
        return active_servers

# Instância única para ser usada em toda a aplicação
server_manager = ServerManager()