from schemas.course import CourseRead, LanguageRead, LevelRead
from .factory import CustomFactoryBase
import factory

from models.course import Language, Level, Course


class LanguageFactory(CustomFactoryBase):
    class _Config:
        factory_model = Language
        factory_model_schema = LanguageRead
        unique_fields = ('name', )
    
    name = factory.Faker('word')

class LevelFactory(CustomFactoryBase):
    class _Config:
        factory_model = Level
        factory_model_schema = LevelRead
        unique_fields = ('code',)
    
    code = factory.Sequence(lambda n: f"level {n}")
    description = factory.Faker('sentence')

class CourseFactory(CustomFactoryBase):
    class _Config:
        factory_model = Course
        factory_model_schema = CourseRead

    name = factory.Faker('word')
    price = factory.Faker('random_int')
    description = factory.Faker('paragraph', nb_sentences=10)
    language = factory.SubFactory(LanguageFactory)
    level = factory.SubFactory(LevelFactory)


    