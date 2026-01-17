from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import servers, console

app = FastAPI(title="Game Server Manager")

app.include_router(servers.router)
app.include_router(console.router)

app.mount("/", StaticFiles(directory="app/web", html=True), name="web")
