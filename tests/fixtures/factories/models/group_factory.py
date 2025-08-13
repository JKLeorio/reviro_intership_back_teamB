from datetime import timedelta
from schemas.group import GroupResponse

import factory
from .factory import CustomFactoryBase
from .course_factory import CourseFactory
from .user_factory import UserFactory
from models.group import Group

class GroupFactory(CustomFactoryBase):
    class _Config:
        factory_model = Group
        factory_model_schema = GroupResponse

    name = factory.Faker('name')
    start_date = factory.Faker('date_between_dates', date_end='now', date_start='now' )
    end_date = factory.LazyAttribute(lambda ob: ob.start_date + timedelta(days=30))
    approximate_lesson_start = factory.Faker('time_object')
    course = factory.SubFactory(CourseFactory)
    # is_active = factory.Faker('pybool')
    # is_archived = factory.Faker('pybool')
    is_active = True
    is_archived = False
    teacher = factory.SubFactory(UserFactory)