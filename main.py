import uvicorn
from fastapi import FastAPI
from api.routers import authRouter


app = FastAPI()

app.include_router(authRouter, prefix="/auth", tags=["auth"])

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
    )
