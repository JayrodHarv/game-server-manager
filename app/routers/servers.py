from fastapi import APIRouter, HTTPException
from app.games.registry import GAME_REGISTRY
from app.docker_runtime import start_container

router = APIRouter(prefix="/servers")


@router.post("/")
def create_server(payload: dict):
    game_name = payload["game"]
    server_name = payload["name"]
    config = payload.get("config", {})

    if game_name not in GAME_REGISTRY:
        raise HTTPException(400, "Unknown game type")

    game = GAME_REGISTRY[game_name]

    start_container(
        name=server_name,
        image=game.image,
        env=game.env(config),
        ports=game.ports,
    )

    return {"status": "started", "server": server_name}
