import uvicorn
from fastapi import FastAPI

from src.routes import auth, users
from src.conf.constant import API

app = FastAPI()

app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
