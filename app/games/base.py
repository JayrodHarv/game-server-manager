from abc import ABC, abstractmethod
from typing import Dict, List


class GameServer(ABC):
    name: str
    image: str
    ports: List[int]

    supports_console: bool = False
    supports_rcon: bool = False

    @abstractmethod
    def env(self, config: Dict) -> Dict[str, str]:
        pass

    @abstractmethod
    def send_command(self, server_name: str, command: str):
        pass