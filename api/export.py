from typing import Optional, Literal, Iterable, Any, List
import io, csv, datetime as dt
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from openpyxl import Workbook

from db.database import get_async_session
from db.types import Role, PaymentDetailStatus
from api.auth import current_admin_user
from models.user import User, student_group_association_table
from models.course import Course
from models.group import Group
from models.payment import PaymentDetail, PaymentCheck
from schemas.group import GroupBase
from schemas.payment import FinanceRow, PaymentCheckShort
from utils.checks_filters import CheckParams, build_checks_query


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


def extensions(format, headers, rows, filename):
    if format == 'csv':
        return StreamingResponse(_csv_stream(headers, rows()), media_type='text/csv',
                                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    bio = _xlsx_bytes(headers, rows())
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment: filename="{filename}"'})


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
    return extensions(format, headers, rows, filename)


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

            finance_map[key] = FinanceRow(
                student_id=user_obj.id,
                student_first_name=user_obj.first_name or "",
                student_last_name=user_obj.last_name or "",
                group_id=group_obj.id,
                payment_detail_id=detail_obj.id if detail_obj else None,
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

    headers = ["ID студента", "Фамилия", "Имя", "Группа", "Курс", "Текущий месяц", "Оплачено (месяц)"]

    def row_data():
        for f in finance_list:
            yield [
                f.student_id,
                f.student_last_name,
                f.student_first_name,
                f.group.name if f.group else "",
                f.group_course_name or "",
                f.current_month_number or "",
                f.months_paid or ""
            ]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"finance_{ts}.{format}"

    return extensions(format, headers, row_data, filename)


@export_router.get('/students')
async def export_student(
        format: Literal['csv', 'xlsx'] = Query("csv"),
        group_id: Optional[int] = None,
        search: Optional[str] = None,
        db: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_admin_user)
):

    q = (
        select(User, Group)
        .join(student_group_association_table,
              student_group_association_table.c.user_id == User.id)
        .join(Group, Group.id == student_group_association_table.c.group_id)
        .where(or_(User.role == getattr(Role, "STUDENT", 'student'),
                   User.role == "student"))
    )

    conds = []
    if group_id is not None:
        g = await db.get(Group, group_id)
        if g is None:
            raise HTTPException(status_code=404, detail="Group not found")
        conds.append(Group.id == group_id)
    if search:
        like = f"%{search}%"
        conds.append(or_(User.first_name.ilike(like), User.last_name.ilike(like)))
    if conds:
        q = q.where(and_(*conds))

    res = await db.execute(q)
    pairs = res.unique().all()

    headers = ["ID", "ФИО", "Группа", "Почта", "Телефон"]

    def rows():
        for u, g in pairs:
            fio = " ".join(filter(None, [getattr(u, "last_name", ""), getattr(u, "first_name", "")])).strip()
            email = getattr(u, "email", "") or ""
            phone = (getattr(u, "phone", None)
                     or getattr(u, "phone_number", None)
                     or getattr(u, "telephone", None)
                     or "")
            yield [u.id, fio, getattr(g, "name", "") or "", email, phone]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"students_{ts}.{format}"
    return extensions(format, headers, rows, filename)


@export_router.get("/teachers")
async def export_teachers(
    format: Literal["csv", "xlsx"] = Query("csv"),
    course_id: Optional[int] = Query(None, description="Фильтр по курсу"),
    search: Optional[str] = Query(None, description="Поиск по имени/фамилии"),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user),
):
    q = (
        select(User, Group)
        .join(Group, Group.teacher_id == User.id)
        .options(selectinload(Group.course))
        .where(or_(User.role == getattr(Role, "TEACHER", "teacher"), User.role == "teacher"))
    )

    conds = []
    if course_id is not None:
        course = await db.get(Course, course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
        conds.append(Group.course_id == course_id)

    if search:
        like = f"%{search}%"
        conds.append(or_(User.first_name.ilike(like), User.last_name.ilike(like)))

    if conds:
        q = q.where(and_(*conds))

    res = await db.execute(q)
    pairs = res.unique().all()

    headers = ["ID", "ФИО", "Курс", "Почта", "Телефон"]

    def rows():
        seen = set()
        for u, g in pairs:
            key = (u.id, getattr(g, "course_id", None))
            if key in seen:
                continue
            seen.add(key)

            fio = " ".join(filter(None, [getattr(u, "last_name", ""), getattr(u, "first_name", "")])).strip()
            email = getattr(u, "email", "") or ""
            phone = (getattr(u, "phone", None)
                     or getattr(u, "phone_number", None)
                     or getattr(u, "telephone", None)
                     or "")
            course_name = getattr(getattr(g, "course", None), "name", "") or ""

            yield [u.id, fio, course_name, email, phone]

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"teachers_{ts}.{format}"
    return extensions(format, headers, rows, filename)
