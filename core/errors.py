# core/errors.py
class GameServerError(Exception):
    """Classe base para todas as exceções relacionadas a servidores de jogos."""
    pass

class ServerStartError(GameServerError):
    """Lançada quando há um erro ao iniciar um processo de servidor."""
    pass

class RconConnectionError(GameServerError):
    """Lançada quando a comunicação RCON falha."""
    pass

class ServerNotFoundError(GameServerError):
    """Lançada quando um ID de servidor não é encontrado na configuração."""
    pass