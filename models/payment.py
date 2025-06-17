from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.dbbase import Base
from db.types import PaymentMethod
from utils.date_time_utils import get_current_time

if TYPE_CHECKING:
    from models.user import User
    from models.course import Course


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    amount: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.CASH)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    user: Mapped["User"] = relationship(back_populates='payments')

    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete='CASCADE'))
    course: Mapped["Course"] = relationship(back_populates='payments')
