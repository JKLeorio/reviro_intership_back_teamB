from datetime import time, timedelta
from db.types import AttendanceStatus
from schemas.lesson import AttendanceBase, AttendanceResponse, ClassroomRead, HomeworkRead, HomeworkReviewRead, HomeworkSubmissionRead, HomeworkSubmissionShort, LessonRead
import factory
from .user_factory import UserFactory
from tests.fixtures.factories.utils import get_enum_randomizer
from .factory import CustomFactoryBase
from utils.date_time_utils import get_current_time, get_week_start_end
from models.lesson import Attendance, Classroom, Homework, HomeworkReview, HomeworkSubmission, Lesson
from .group_factory import GroupFactory

attendance_status_randomizer = get_enum_randomizer(AttendanceStatus)

class ClassroomFactory(CustomFactoryBase):
    class _Config:
        factory_model = Classroom
        factory_model_schema = ClassroomRead
        unique_fields = ('name',)

    name = factory.Faker('name')

class LessonFactory(CustomFactoryBase):
    class _Config:
        factory_model = Lesson
        factory_model_schema = LessonRead

    name = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    link = factory.Faker('uri')
    day = factory.Faker('date_between', start_date=get_week_start_end()[0] , end_date = '+7d')
    lesson_start = factory.Faker('time_object')
    lesson_end = factory.LazyAttribute(
        lambda ob: (
            get_current_time() + timedelta(
                hours=ob.lesson_start.hour+1,
                minutes=ob.lesson_start.minute,
                seconds=ob.lesson_start.second)
            ).time()
        )
    # passed = factory.Faker('pybool')
    passed = False
    teacher = factory.SubFactory(UserFactory)
    group = factory.SubFactory(GroupFactory)
    classroom = factory.SubFactory(ClassroomFactory)
    homework = None

class HomeworkFactory(CustomFactoryBase):
    class _Config:
        factory_model = Homework
        factory_model_schema = HomeworkRead

    description = factory.Faker('paragraph')
    deadline = factory.Faker('date_time_between', start_date = 'now', end_date='+7d')
    file_path = factory.Faker('image_url')
    lesson = factory.SubFactory(LessonFactory)
    submissions = []

class HomeworkSubmissionFactory(CustomFactoryBase):
    class _Config:
        factory_model = HomeworkSubmission
        factory_model_schema = HomeworkSubmissionShort

    homework = factory.SubFactory(HomeworkFactory)
    student = factory.SubFactory(UserFactory)
    file_path = factory.Faker('image_url')
    content = factory.Faker('paragraph', nb_sentences=10)

class HomeworkReviewFactory(CustomFactoryBase):
    class _Config:
        factory_model = HomeworkReview
        factory_model_schema = HomeworkReviewRead

    submission = factory.SubFactory(HomeworkSubmissionFactory)
    teacher = factory.SubFactory(UserFactory)
    comment = factory.Faker('paragraph')

class AttendanceFactory(CustomFactoryBase):
    class _Config:
        factory_model = Attendance
        factory_model_schema = AttendanceBase

    status = factory.LazyAttribute(attendance_status_randomizer)
    student = factory.SubFactory(UserFactory)
    lesson = factory.SubFactory(LessonFactory)