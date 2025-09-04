# from datetime import datetime
# from typing import TYPE_CHECKING
# from db.dbbase import Base
# from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from utils.date_time_utils import get_current_time

# if TYPE_CHECKING:
#     from models.course import Course


# class Enrollment(Base):

#     __tablename__ = "enrollments"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     first_name: Mapped[str] = mapped_column(String, nullable=False)
#     last_name: Mapped[str] = mapped_column(String, nullable=False)

#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

#     email: Mapped[str] = mapped_column(String, nullable=False)
#     phone_number: Mapped[str] = mapped_column(String, nullable=False)

#     is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

#     user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

#     course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
#     course: Mapped["Course"] = relationship(back_populates="enrollments")
