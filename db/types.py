from enum import Enum


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


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


class PaymentMethod(str, Enum):
    CASH = 'cash'
    CARD = 'card'
    TRANSFER = 'transfer'
