from enum import Enum
from dataclasses import dataclass

@dataclass
class PyChatConfig:
    name: str
    port: int
    timeout: int
    host_ip: str

@dataclass
class PyChatConfigs:
    configs: dict[str, PyChatConfig]
    most_recent: str
    
class PyChatConfigStatus(Enum):
    ALREADY_EXISTS = -1
    JSON_ERROR = -2
    IO_ERROR = -3
    SUCCESS = 1