import asyncio
import threading
from queue import Queue, Empty
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.docker_runtime import get_container
from app.games.registry import GAME_REGISTRY

router = APIRouter()

@router.websocket("/ws/servers/{server_name}")
async def console_ws(websocket: WebSocket, server_name: str):
    await websocket.accept()

    try:
        container = get_container(server_name)
    except Exception:
        await websocket.send_text("Container not found")
        await websocket.close()
        return

    game = GAME_REGISTRY["minecraft"]

    stop_event = threading.Event()
    message_queue: Queue[str] = Queue()

    # LOG THREAD (producer)
    def stream_logs():
        buffer = ""
        try:
            for chunk in container.logs(stream=True, follow=True, tail=20):
                if stop_event.is_set():
                    break

                buffer += chunk.decode(errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    message_queue.put(line)
        except Exception as e:
            message_queue.put(f"[log error] {e}")

    threading.Thread(target=stream_logs, daemon=True).start()

    # ASYNC SENDER (consumer)
    async def send_loop():
        while True:
            try:
                line = message_queue.get_nowait()
                await websocket.send_text(line)
            except Empty:
                await asyncio.sleep(0.01)
            except Exception:
                break

    sender_task = asyncio.create_task(send_loop())

    try:
        while True:
            command = await websocket.receive_text()
            if command.strip():
                asyncio.create_task(
                    asyncio.to_thread(
                        game.send_command,
                        server_name,
                        command
                    )
                )

    except WebSocketDisconnect:
        stop_event.set()
        sender_task.cancel()
