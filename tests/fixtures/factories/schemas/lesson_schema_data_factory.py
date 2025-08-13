from datetime import date, time, timedelta, datetime
from factory import Factory, Faker, lazy_attribute
from factory.fuzzy import FuzzyDate, FuzzyDateTime

from utils.date_time_utils import get_current_time, get_week_start_end

class LessonCreateDataFactory(Factory):
    class Meta:
        model = dict

    name = Faker("sentence", nb_words=3)
    description = Faker("paragraph", nb_sentences=2)
    link = Faker("uri")

    @lazy_attribute
    def day(self) -> str:
        return get_current_time().date().isoformat()

    @lazy_attribute
    def lesson_start(self) -> str:
        return get_current_time().time().isoformat()

    @lazy_attribute
    def lesson_end(self) -> str:
        dt_start = get_current_time()
        dt_end = dt_start + timedelta(minutes=30)
        return dt_end.time().isoformat()

    teacher_id = None
    classroom_id = None
    passed = False
        