from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/arcaea/assets", StaticFiles(directory="/opt/arcaea/assets"), name="static")


@app.get("/")
async def check_health():
    return {"status": "ok"}
