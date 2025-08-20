from enum import Enum

from pydantic import HttpUrl
from sqlalchemy import String, TypeDecorator


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Level(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"

    FAILED = "failed"

    REFUNDED = "refunded"
    CANCELED = "canceled"


class PaymentDetailStatus(str, Enum):
    PAID = 'Оплачено'
    UNPAID = 'Не оплачено'


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    bank_transfer = "bank_transfer"
    online = "online"
    promo = "promo"
    stripe = "stripe"


class Currency(str, Enum):
    KGS = "KGS"
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    UZS = "UZS"
    KZT = "KZT"


class HttpUrlType(TypeDecorator):
    impl = String(2083)
    cache_ok = True
    python_type = HttpUrl

    def process_bind_param(self, value, dialect) -> str:
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect) -> HttpUrl:
        if value is not None:
            return HttpUrl(value)
        return value

    def process_literal_param(self, value, dialect) -> str:
        return str(value)


class AttendanceStatus(str, Enum):
    ATTENTED = 'attended'
    ABSENT = 'absent'
