from datetime import datetime, date
from typing import List
from db.dbbase import Base
from sqlalchemy import DateTime, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from utils.date_time_utils import get_current_time
from models.lesson import Lesson
from models.course import Course


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import student_group_association_table, User
    from models.lesson import Lesson


class Group(Base):
    from models.payment import Payment
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id', ondelete="CASCADE"))
    course: Mapped['Course'] = relationship(back_populates="groups")

    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    teacher: Mapped["User"] = relationship(back_populates="groups_taught")

    lessons: Mapped[List["Lesson"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    students: Mapped[List["User"]] = relationship(secondary="student_group_association_table",
                                                     back_populates="groups_joined")
    payments: Mapped[list["Payment"]] = relationship(back_populates="group")
