from datetime import datetime
from typing import List, Annotated, TYPE_CHECKING
from utils.date_time_utils import get_current_time
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.dbbase import Base

if TYPE_CHECKING:
    from models.group import Group


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

    courses: Mapped[List["Course"]] = relationship(back_populates='level')


class Course(Base):
    __tablename__ = 'courses'

    id: Mapped[idpk]
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    language_id: Mapped[int] = mapped_column(ForeignKey('languages.id', ondelete="CASCADE"))
    level_id: Mapped[int] = mapped_column(ForeignKey('levels.id', ondelete="CASCADE"))
    created_at: Mapped[created_at]

    language: Mapped["Language"] = relationship(back_populates='courses')
    level: Mapped["Level"] = relationship(back_populates='courses')

    groups: Mapped[List["Group"]] = relationship(back_populates="course", cascade='all, delete-orphan')
