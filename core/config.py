# core/config.py
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Optional

class AppSecrets(BaseSettings):
    """Carrega segredos do arquivo .env"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    discord_bot_token: str
    minecraft_rcon_password: str
    factorio_rcon_password: str

class RconConfig(BaseModel):
    host: str
    port: int
    password: Optional[str] = None # Tornamos a senha opcional aqui

class ServerConfig(BaseModel):
    name: str
    game_type: str
    path: str
    start_command: List[str]
    mention_role_id: int
    rcon: RconConfig

class BotConfig(BaseModel):
    guild_id: int
    notification_channel_id: int
    admin_notification_channel_id: int
    authorized_role_id: int

class MainConfig(BaseModel):
    bot: BotConfig
    servers: Dict[str, ServerConfig]

def load_config() -> MainConfig:
    """Carrega as configurações do YAML e injeta os segredos."""
    secrets = AppSecrets()
    with open("config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Injeta as senhas RCON lidas do .env no objeto de configuração
    if 'minecraft' in config_data['servers']:
        config_data['servers']['minecraft']['rcon']['password'] = secrets.minecraft_rcon_password
    if 'factorio' in config_data['servers']:
        config_data['servers']['factorio']['rcon']['password'] = secrets.factorio_rcon_password

    return MainConfig(**config_data)

# Instâncias globais para serem importadas facilmente em outros módulos
secrets = AppSecrets()
config = load_config()