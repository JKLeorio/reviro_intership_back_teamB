from typing import Optional, Literal, Iterable, Callable, Tuple, Dict, Any, List
import io, csv, datetime as dt
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from openpyxl import Workbook

from db.database import get_async_session
from api.auth import current_admin_user
from models.user import User
from models.group import Group
from models.payment import PaymentDetail, PaymentCheck
from schemas.group import GroupBase
from schemas.payment import FinanceRow, PaymentCheckShort
from utils.checks_filters import CheckParams, build_checks_query
from api.finance import get_finance


export_router = APIRouter(prefix='/export', tags=["Export"])


def _csv_stream(headers: List[str], rows: Iterable[List[Any]]):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers); yield buf.getvalue(); buf.seek(0); buf.truncate(0)

    for r in rows:
        w.writerow(r)
        yield buf.getvalue()
        buf.seek(0); buf.truncate(0)


def _xlsx_bytes(headers: List[str], rows: Iterable[List[Any]]):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title="Export", index=0)
    ws.append(headers)
    for r in rows:
        ws.append(r)
    bio = io.BytesIO(); wb.save(bio); bio.seek(0)
    return bio


@export_router.get('/checks')
async def export_checks(
        format: Literal['csv', 'xlsx'] = Query("csv"),
        student_id: Optional[int] = Query(None),
        group_id: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_admin_user)
):
    params = CheckParams(group_id=group_id, student_id=student_id)
    q = build_checks_query(params).order_by(desc(PaymentCheck.uploaded_at))
    items = await db.execute(q)
    items = items.unique().scalars().all()
    headers = ["ID", "Файл", "Студент",  "Группа", "Стоимость", "Загружен"]

    def rows():
        for c in items:
            student = getattr(c, "student", None)
            group = getattr(c, "group", None)
            course = getattr(group, "course", None)

            fio = " ".join(filter(None, [
                getattr(student, "last_name", ''),
                getattr(student, "first_name", '')
            ])).strip()
            price = getattr(course, "price", '')
            uploaded = c.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if c.uploaded_at else ""

            yield [
                c.id,
                c.check or '',
                fio,
                getattr(group, "name", '') or '',
                price,
                uploaded
            ]
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"checks_{ts}.{format}"
    if format == 'csv':
        return StreamingResponse(_csv_stream(headers, rows()), media_type='text/csv',
                                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    bio = _xlsx_bytes(headers, rows())
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment: filename="{filename}"'})


@export_router.get('/finance')
async def export_finance(
        format: Literal['csv', 'xlsx'] = Query("csv"),
        group_id: Optional[int] = None,
        search: Optional[str] = None,
        db: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_admin_user)
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
            status_str = (
                detail_obj.status.value
                if (detail_obj and getattr(detail_obj, "status", None) is not None and hasattr(detail_obj.status,
                                                                                               "value"))
                else (
                    str(detail_obj.status) if detail_obj and getattr(detail_obj, "status", None) is not None else None)
            )
            finance_map[key] = FinanceRow(
                student_id=user_obj.id,
                student_first_name=user_obj.first_name or "",
                student_last_name=user_obj.last_name or "",
                group_id=group_obj.id,
                payment_detail_id=detail_obj.id if detail_obj else None,
                payment_status=status_str,
                current_month_number=detail_obj.current_month_number,
                months_paid=detail_obj.months_paid,
                group=GroupBase.model_validate(group_obj),
                group_course_name=getattr(getattr(group_obj, "course", None), "name", None),
                checks=[],
            )
        if check_obj:
            finance_map[key].checks.append(PaymentCheckShort.model_validate(check_obj))

    finance_list = sorted(
        finance_map.values(),
        key=lambda x: (x.student_last_name.lower(), x.student_first_name.lower())
    )

    headers = ["ID студента", "Фамилия", "Имя", "Группа", "Курс", "Текущий месяц", "Оплачено за месяц", "Статус оплаты"]

    def row_data():
        for f in finance_list:
            yield [
                f.student_id,
                f.student_last_name,
                f.student_first_name,
                f.group.name if f.group else "",
                f.group_course_name or "",
                f.current_month_number or "",
                f.months_paid or "",
                f.payment_status or ""
            ]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"finance_{ts}.{format}"

    if format == 'csv':
        return StreamingResponse(_csv_stream(headers, row_data()), media_type='text/csv',
                                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    bio = _xlsx_bytes(headers, row_data())
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})
