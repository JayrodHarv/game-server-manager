from fastapi import APIRouter, HTTPException
from app.docker_client import run_container, get_container, list_containers
from app.models import ServerCreate, ServerUpdate
from mcrcon import MCRcon
import os

router = APIRouter(prefix="/servers", tags=["servers"])

BASE_DIR = "/srv/servers"

@router.post("/")
def create_server(server: ServerCreate):
    server_dir = os.path.join(BASE_DIR, server.name)
    os.makedirs(server_dir, exist_ok=True)

    # ports mapping: game port plus optional RCON port
    ports = {"25565/tcp": server.port}

    # environment variables to pass to the container
    env = {}

    if server.rcon_password:
        # enable RCON in the Minecraft image
        env.update({
            "ENABLE_RCON": "true",
            "RCON_PORT": str(server.rcon_port),
            "RCON_PASSWORD": server.rcon_password,
        })
        # expose RCON port on the host as well
        ports[f"{server.rcon_port}/tcp"] = server.rcon_port

    try:
        container = run_container(
            image=server.image,
            name=server.name,
            ports=ports,
            volumes={
                server_dir: {"bind": "/data", "mode": "rw"}
            },
            memory=server.memory,
            cpus=server.cpus,
            env=env,
        )
        return {"status": "created", "id": container.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/start")
def start_server(name: str):
    container = get_container(name)
    container.start()
    return {"status": "started"}


@router.post("/{name}/stop")
def stop_server(name: str):
    container = get_container(name)
    container.stop()
    return {"status": "stopped"}


@router.delete("/{name}")
def delete_server(name: str, force: bool = False):
    """Stop (if running) and remove a container.

    Query params:
      - force: bool = If true, force removal even if stop fails
    """
    try:
        container = get_container(name)

        # If the container is running, try to stop it gracefully first
        try:
            if container.status == "running":
                container.stop(timeout=10)
        except Exception:
            if not force:
                raise HTTPException(status_code=500, detail="Container is running and failed to stop; retry with ?force=true to force removal")

        # Remove the container (force option will kill if necessary)
        container.remove(force=force)

        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/update")
def update_server(name: str, update: ServerUpdate):
    """Update server settings by recreating the container with new settings.

    This stops and removes the existing container (if present) and starts a new one
    with the updated configuration. The server's data directory is preserved.
    """
    server_dir = os.path.join(BASE_DIR, name)

    try:
        container = get_container(name)

        # fetch current attributes
        attrs = container.attrs
        # attempt to preserve image used previously
        image = container.image.tags[0] if container.image.tags else container.image.id

        # parse existing env into a dict
        env_list = attrs.get("Config", {}).get("Env", []) or []
        current_env = {k: v for k, v in (s.split("=", 1) for s in env_list if "=" in s)}

        # ports: try to preserve existing host ports
        ports = {}
        port_bindings = attrs.get("HostConfig", {}).get("PortBindings") or {}
        if "25565/tcp" in port_bindings and port_bindings["25565/tcp"]:
            ports["25565/tcp"] = int(port_bindings["25565/tcp"][0].get("HostPort"))

        # apply requested changes
        if update.port:
            ports["25565/tcp"] = update.port

        # RCON handling
        current_rcon_port = int(current_env.get("RCON_PORT")) if current_env.get("RCON_PORT") else None
        current_rcon_pass = current_env.get("RCON_PASSWORD")

        target_rcon_pass = update.rcon_password if update.rcon_password is not None else current_rcon_pass
        target_rcon_port = update.rcon_port if update.rcon_port is not None else current_rcon_port

        env = {}
        if target_rcon_pass:
            env.update({
                "ENABLE_RCON": "true",
                "RCON_PORT": str(target_rcon_port or 25575),
                "RCON_PASSWORD": target_rcon_pass,
            })
            ports[f"{env['RCON_PORT']}/tcp"] = int(env["RCON_PORT"])

        # resources
        memory = update.memory if update.memory else None
        cpus = update.cpus if update.cpus else None

        # stop and remove current container
        try:
            if container.status == "running":
                container.stop(timeout=10)
        except Exception:
            # ignore stop errors — we'll attempt removal and allow caller to force if needed
            pass

        container.remove()

        # recreate container with merged settings
        new_container = run_container(
            image=update.image if update.image else image,
            name=name,
            ports=ports,
            volumes={
                server_dir: {"bind": "/data", "mode": "rw"}
            },
            memory=memory or "2g",
            cpus=cpus or 1.0,
            env=env,
        )

        return {"status": "updated", "id": new_container.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def list_servers():
    containers = list_containers()
    return [
        {
            "name": c.name,
            "status": c.status,
            "image": c.image.tags,
        }
        for c in containers
    ]


@router.get("/{name}/logs")
def server_logs(name: str):
    try:
        container = get_container(name)

        logs = container.logs(tail=200)

        # Docker may return bytes OR str
        if isinstance(logs, bytes):
            logs = logs.decode(errors="ignore")

        return {"logs": logs}

    except Exception as e:
        return {
            "error": str(e),
            "hint": "Check that the container exists and is running"
        }
