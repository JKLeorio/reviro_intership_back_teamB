import uvicorn
from fastapi import FastAPI
from api.routers import authRouter
from api.course import course_router, language_router, level_router

app = FastAPI()

app.include_router(authRouter, prefix="/auth", tags=["auth"])
app.include_router(course_router, prefix="/courses", tags=["Courses"])
app.include_router(language_router, prefix="/languages", tags=["Languages"])
app.include_router(level_router, prefix="/levels", tags=["Levels"])


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
    )
