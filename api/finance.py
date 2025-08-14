from math import ceil
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from api.auth import current_admin_user
from db.database import get_async_session
from models.group import Group
from models.payment import PaymentCheck, PaymentDetail
from models.user import User
from schemas.group import GroupBase
from schemas.pagination import PaginatedResponse, Pagination
from schemas.payment import FinanceRow, PaymentCheckShort

finance_router = APIRouter()


@finance_router.get("", response_model=PaginatedResponse[FinanceRow])
async def get_finance(
    group_id: Optional[int] = None,
    search: Optional[str] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user),
):
    q = (
        select(User, Group, PaymentDetail, PaymentCheck)
        .join(PaymentDetail, PaymentDetail.student_id == User.id)
        .join(Group, Group.id == PaymentDetail.group_id)
        .outerjoin(
            PaymentCheck,
            and_(
                PaymentCheck.student_id == User.id,
                PaymentCheck.group_id == Group.id,
            ),
        )
        .options(selectinload(Group.course))
    )

    conds = []
    g = await db.get(Group, group_id)
    if group_id and g is None:
        raise HTTPException(404, detail="Group not found")
    if group_id is not None:
        conds.append(PaymentDetail.group_id == group_id)
    if search:
        like = f"%{search}%"
        conds.append(
            or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                PaymentCheck.check.ilike(like),
            )
        )
    if conds:
        q = q.where(and_(*conds))

    res = await db.execute(q)
    rows = res.unique().all()

    finance_map: dict[tuple[int, int], FinanceRow] = {}

    for user_obj, group_obj, detail_obj, check_obj in rows:
        key = (user_obj.id, group_obj.id)
        if key not in finance_map:
            course_name = getattr(getattr(group_obj, "course", None), "name", None)

            finance_map[key] = FinanceRow(
                student_id=user_obj.id,
                student_first_name=user_obj.first_name or "",
                student_last_name=user_obj.last_name or "",
                group_id=group_obj.id,
                payment_detail_id=detail_obj.id if detail_obj else None,
                current_month_number=(
                    detail_obj.current_month_number if detail_obj else None
                ),
                months_paid=detail_obj.months_paid if detail_obj else None,
                payment_status=detail_obj.status if detail_obj else None,
                group=GroupBase.model_validate(group_obj),
                group_course_name=course_name,
                checks=[],
            )
        if check_obj:
            finance_map[key].checks.append(PaymentCheckShort.model_validate(check_obj))

    finance_list = sorted(
        finance_map.values(),
        key=lambda x: (x.student_last_name.lower(), x.student_first_name.lower()),
    )

    total_items = len(finance_list)
    total_pages = max(1, ceil(total_items / size))
    if page > total_pages:
        page = total_pages

    start = (page - 1) * size
    end = start + size
    paginated_items = finance_list[start:end]

    return PaginatedResponse[FinanceRow](
        items=paginated_items,
        pagination=Pagination(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            current_page_size=len(paginated_items),
        ),
    )
