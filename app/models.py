from typing import Optional
from pydantic import BaseModel

class ServerCreate(BaseModel):
    name: str
    image: str = "itzg/minecraft-server"
    port: int = 25565
    memory: str = "2g"
    cpus: float = 1.0

    # RCON settings (optional)
    rcon_port: int = 25575
    rcon_password: Optional[str] = None


class ServerUpdate(BaseModel):
    """Partial update model for server settings.

    All fields are optional; unspecified fields are preserved where possible.
    """
    image: Optional[str] = None
    port: Optional[int] = None
    memory: Optional[str] = None
    cpus: Optional[float] = None
    rcon_port: Optional[int] = None
    rcon_password: Optional[str] = None
