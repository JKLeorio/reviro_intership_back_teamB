import uvicorn
import logging
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqladmin import Admin
from contextlib import asynccontextmanager

from admin.course import CourseAdmin, LanguageAdmin, LevelAdmin
from admin.group import GroupAdmin
from admin.lesson import AttendanecAdmin, ClassroomAdmin
from db.database import get_async_session, engine

from api.enrollment import enrollment_router
from api.auth import authRouter
from api.course import course_router, language_router, level_router
from api.lesson import (lesson_router, classroom_router, homework_router, homework_submission_router,
                        homework_review_router)
from api.group import group_students_router, group_router
from api.user import user_router
from api.payment import payment_router, subscription_router, payment_details, update_and_check_payments, \
    payment_requisites, payment_checks_router, stripe_router

from api.shedule import shedule_router
from api.lesson_attendance import attendance_router
from admin.auth import admin_authentication_backend
from api.finance import finance_router
from api.export import export_router
from utils.smtp_client import init_smtp, send_email

scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)


from decouple import config
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"STRIPE_SECRET_KEY: {config('STRIPE_SECRET_KEY', default='Not found')}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Lifespan started")
    try:
        trigger = CronTrigger(hour=0, minute=0)
        scheduler.add_job(update_and_check_payments, trigger)
        scheduler.start()
        logging.info("Scheduler started")
        # app.state.smtp_client = await init_smtp()
        # logging.info("SMTP started")
        yield
    finally:
        scheduler.shutdown()
        logging.info("Scheduler stopped")
        # if getattr(app.state, "smtp_client", None) is not None:
        #     try:
        #         await app.state.smtp_client.quit()
        #         logging.info("SMTP stopped")
        #     except Exception as e:
        #         logging.warning(f"Error closing SMTP client: {e}")

app = FastAPI(lifespan=lifespan)

admin = Admin(app, engine, authentication_backend=admin_authentication_backend)

admin.add_view(GroupAdmin)
admin.add_view(LanguageAdmin)
admin.add_view(LevelAdmin)
admin.add_view(ClassroomAdmin)
admin.add_view(CourseAdmin)
admin.add_view(AttendanecAdmin)


origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/media", StaticFiles(directory="media"), name="media")


app.include_router(shedule_router, prefix='/shedule', tags=['Schedule'])
app.include_router(authRouter, prefix="/auth", tags=["Auth"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
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
app.include_router(homework_review_router, prefix='/homework_review', tags=['Homeworks-review'])
app.include_router(payment_router, prefix='/payment', tags=['Payments'])
app.include_router(payment_details, prefix='/payment_details', tags=['Payment-details'])
app.include_router(subscription_router, prefix='/subscription', tags=['Subscriptions'])
app.include_router(user_router, prefix='/user', tags=['Users'])
app.include_router(payment_requisites, prefix='/payment_requisites', tags=['Payment-requisites'])
app.include_router(payment_checks_router, prefix='/checks', tags=["Payment-checks"])
app.include_router(export_router)
app.include_router(finance_router, prefix='/finance', tags=['Finance'])
app.include_router(stripe_router, prefix='/stripe', tags=['Stripe-payments'])




if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
    )
