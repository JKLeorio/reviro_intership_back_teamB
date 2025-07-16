import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.enrollment import enrollment_router
from api.auth import authRouter
from api.course import course_router, language_router, level_router
from api.lesson import lesson_router, classroom_router, homework_router, homework_submission_router
from api.group import group_students_router, group_router
from api.user import user_router
from api.payment import payment_router, subscription_router
from api.shedule import shedule_router

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/media", StaticFiles(directory="media"), name="media")


app.include_router(shedule_router, prefix='/shedule', tags=['Shedule'])

app.include_router(authRouter, prefix="/auth", tags=["Auth"])
app.include_router(enrollment_router, prefix="/enrollment", tags=["Enrollments"])
app.include_router(course_router, prefix="/courses", tags=["Courses"])
app.include_router(language_router, prefix="/languages", tags=["Languages"])
app.include_router(level_router, prefix="/levels", tags=["Levels"])
app.include_router(group_router, prefix="/group", tags=["group"])
app.include_router(group_students_router, prefix="/group-students", tags=["group-students"])
app.include_router(lesson_router, prefix='/lessons', tags=['Lessons'])
app.include_router(classroom_router, prefix='/classrooms', tags=['Classrooms'])
app.include_router(homework_router, prefix='/homeworks', tags=['Homeworks-teacher'])
app.include_router(homework_submission_router, prefix='/submissions', tags=['Homeworks-student'])
app.include_router(payment_router, prefix='/payment', tags=['Payments'])
app.include_router(subscription_router, prefix='/subscription', tags=['Subscriptions'])
app.include_router(user_router, prefix='/user', tags=['Users'])

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
    )
