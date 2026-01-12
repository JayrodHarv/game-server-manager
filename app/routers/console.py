from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.docker_client import get_container
import asyncio
import threading
from mcrcon import MCRcon

router = APIRouter()

async def _send_rcon_command(host: str, port: int, password: str, command: str):
    # run blocking RCON call in a thread
    def _send():
        with MCRcon(host, password, port=port) as m:
            return m.command(command)

    return await asyncio.to_thread(_send)

@router.websocket("/ws/servers/{name}")
async def websocket_console(websocket: WebSocket, name: str):
    await websocket.accept()

    try:
        container = get_container(name)
    except Exception:
        await websocket.send_text("ERROR: Container not found")
        await websocket.close()
        return

    loop = asyncio.get_event_loop()

    # ---- LOG STREAM THREAD ----
    def stream_logs():
        try:
            for line in container.logs(stream=True, follow=True):
                asyncio.run_coroutine_threadsafe(
                    websocket.send_text(line.decode(errors="ignore")),
                    loop
                )
        except Exception:
            pass

    log_thread = threading.Thread(target=stream_logs, daemon=True)
    log_thread.start()

    # Gather possible RCON configuration from the container
    rcon_password = None
    rcon_port = None
    host_port = None

    try:
        env_list = container.attrs.get("Config", {}).get("Env", []) or []
        env = {k: v for k, v in (s.split("=", 1) for s in env_list if "=" in s)}

        rcon_password = env.get("RCON_PASSWORD")
        if env.get("RCON_PORT"):
            try:
                rcon_port = int(env.get("RCON_PORT"))
            except ValueError:
                rcon_port = None

        # try to get host mapped port for RCON
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
        if rcon_port and f"{rcon_port}/tcp" in ports and ports[f"{rcon_port}/tcp"]:
            host_port = int(ports[f"{rcon_port}/tcp"][0].get("HostPort"))

    except Exception:
        # ignore parsing errors; we'll fallback to exec if needed
        pass

    # ---- RECEIVE COMMANDS ----
    try:
        while True:
            command = await websocket.receive_text()

            # If RCON is configured, send via RCON; otherwise fallback to exec_run
            # if rcon_password and (host_port or rcon_port):
            #     host = "127.0.0.1"
            #     port_to_use = host_port or rcon_port
            #     try:
            #         resp = await _send_rcon_command(host, port_to_use, rcon_password, command)
            #         # Some RCON libraries return empty string for success; indicate OK
            #         await websocket.send_text(resp or "RCON: OK")
            #     except Exception as e:
            #         await websocket.send_text(f"ERROR: RCON command failed: {e}")
            # else:
            #     # fallback to running a command inside the container
            #     container.exec_run(
            #         cmd=command,
            #         stdin=False,
            #         tty=False
            #     )
            # fallback to running a command inside the container
            container.exec_run(
                cmd=command,
                stdin=False,
                tty=False
            )
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"ERROR: {str(e)}")
