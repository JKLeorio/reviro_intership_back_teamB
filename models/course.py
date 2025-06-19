from datetime import datetime
from typing import List, Annotated, TYPE_CHECKING
from utils.date_time_utils import get_current_time
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.dbbase import Base

if TYPE_CHECKING:
    from models.group import Group
    from models.enrollment import Enrollment
    #from models.payment import Subscription


idpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), default=get_current_time)]


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[idpk]
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    courses: Mapped[List["Course"]] = relationship(back_populates="language")


class Level(Base):

    __tablename__ = "levels"

    id: Mapped[idpk]

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=True)

    courses: Mapped[List["Course"]] = relationship(back_populates='level', cascade="all, delete-orphan",
                                                   passive_deletes=True)


class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[idpk]
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=True)

    language_id: Mapped[int] = mapped_column(ForeignKey('languages.id', ondelete="CASCADE"))
    level_id: Mapped[int] = mapped_column(ForeignKey('levels.id', ondelete="CASCADE"))
    created_at: Mapped[created_at]

    language: Mapped["Language"] = relationship(back_populates='courses')
    level: Mapped["Level"] = relationship(back_populates='courses')

    groups: Mapped[List["Group"]] = relationship(back_populates="course", cascade='all, delete-orphan')
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates='course', cascade="all, delete-orphan")

    @property
    def language_name(self) -> str | None:
        return self.language.name if self.language else None

    @property
    def level_code(self) -> str | None:
        return self.level.code if self.level else None


    #Временно cascade
    #subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="course", cascade="all, delete-ophan")
