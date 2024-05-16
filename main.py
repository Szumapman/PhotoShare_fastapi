import uvicorn
from fastapi import FastAPI

from src.routes import auth
from src.conf.constant import API

app = FastAPI()

app.include_router(auth.router, prefix=API)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
