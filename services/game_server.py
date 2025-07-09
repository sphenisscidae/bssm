# services/game_server.py
from abc import ABC, abstractmethod
from core.config import ServerConfig
import subprocess

class GameServer(ABC):
    """
    Interface abstrata que define o contrato para um servidor de jogo gerenciável.
    """
    def __init__(self, server_id: str, config: ServerConfig):
        self.server_id = server_id
        self.config = config
        self.process: subprocess.Popen | None = None

    @abstractmethod
    async def start(self) -> str:
        """Inicia o servidor e retorna uma mensagem de sucesso."""
        pass

    @abstractmethod
    async def stop(self, force: bool = False) -> str:
        """Para o servidor e retorna uma mensagem de sucesso."""
        pass

    @abstractmethod
    async def get_status(self) -> str:
        """Retorna uma string formatada com o status detalhado do servidor."""
        pass

    def is_running(self) -> bool:
        """Verifica se o processo do servidor está ativo."""
        return self.process is not None and self.process.poll() is None