from fastapi import FastAPI
from app.routers import servers, console

app = FastAPI(title="Game Server Manager")

app.include_router(servers.router)
app.include_router(console.router)

@app.get("/")
def root():
    return {"status": "ok"}
