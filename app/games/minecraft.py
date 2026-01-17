from app.games.base import GameServer
from app.docker_runtime import get_container, get_stdin_socket
from docker import from_env

docker = from_env()

class MinecraftServer(GameServer):
    name = "minecraft"
    image = "itzg/minecraft-server"
    ports = [25565]

    supports_console = True
    supports_rcon = True

    def env(self, config):
        return {
            "EULA": "TRUE",
            "VERSION": config.get("version", "latest"),
            "ENABLE_RCON": "TRUE",
            "RCON_PASSWORD": config["rcon_password"],
            "RCON_PORT": "25575",
        }

    def send_command(self, server_name: str, command: str):
        container = get_container(server_name)
        sock = get_stdin_socket(container)

        data = (command.strip() + "\n").encode("utf-8")
        sock._sock.send(data)
