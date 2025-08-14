from dataclasses import dataclass
from typing import Optional, Tuple, List
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
from models.payment import PaymentCheck, PaymentDetail
from models.user import User
from models.group import Group


@dataclass
class CheckParams:
    group_id: Optional[int] = None
    student_id: Optional[int] = None


def apply_filters(q, params: CheckParams):
    conds = []
    if params.group_id is not None:
        conds.append(PaymentCheck.group_id == params.group_id)
    if conds:
        q = q.where(and_(*conds))
    return q


def build_checks_query(params: CheckParams):
    q = (
        select(PaymentCheck)
        .outerjoin(PaymentCheck.student)
        .outerjoin(PaymentCheck.group)
        .options(
            selectinload(PaymentCheck.student),
            selectinload(PaymentCheck.group).selectinload(Group.course)
        )
    )

    return apply_filters(q, params)


def build_finance_query(params: CheckParams):
    sub_checks = (
        select(PaymentCheck.student_id, PaymentCheck.group_id)
        .group_by(PaymentCheck.student_id, PaymentCheck.group_id)
        .subquery()
    )
    q = (
        select(
            User.id.label('student_id'),
            User.first_name.label('student_first_name'),
            User.last_name.label('student_last_name'),
            Group.id.label('group_id'),
            Group.name.label('group_name'),
            PaymentDetail.id.label("payment_detail_id"),
            PaymentDetail.status.label('payment_status'),
        )
        .join(PaymentDetail, and_(PaymentDetail.student_id == User.id, PaymentDetail.group_id == Group.id))
        .outerjoin(sub_checks, and_(sub_checks.c.student_id == User.id, sub_checks.c.group_id == Group.id))
    )

    return apply_filters(q, params)
