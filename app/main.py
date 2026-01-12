from fastapi import FastAPI
from app.routers import servers, console
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Game Server Manager")

app.include_router(servers.router)
app.include_router(console.router)

app.mount("/", StaticFiles(directory="web", html=True), name="web")