from models import PaymentDetail, Group, User
from datetime import date
from db.types import PaymentDetailStatus
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def create_test_payment(session: AsyncSession):

    student = User(email="student@test.com", hashed_password="123", is_active=True, first_name="Test", last_name='Test',
                   role='student')
    group = Group(name="Test Group", start_date=date.today(), end_date=date.today(), course_id=1, teacher_id=1,
                  is_active=True, is_archived=False)
    session.add_all([student, group])
    await session.flush()

    payment = PaymentDetail(
        student_id=student.id,
        group_id=group.id,
        price=100.0,
        joined_at=date.today(),
        months_paid=1,
        current_month_number=1,
        deadline=date.today(),
        status=PaymentDetailStatus.PAID,
        is_active=True
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


@pytest.mark.anyio
async def test_get_payment_detail_by_id(client, create_test_payment):
    payment = create_test_payment
    response = await client.get(
        f"/payment_details/payments/?group_id={payment.group_id}",
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_get_payment_detail_by_id(client, create_test_payment):
    payment = create_test_payment
    response = await client.get(
        f"/payment_details/?payment_id={payment.id}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payment.id
    assert data["status"] in ["Оплачено", "Не оплачено"]


@pytest.mark.anyio
async def test_update_payment_detail(client):
    response = await client.patch(
        f"/payment_details/?payment_id=3",
        json={"months_paid": 5, "current_month_number": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["months_paid"] == 5
    assert data["current_month_number"] == 3
    assert data["status"] == "Оплачено"


@pytest.mark.anyio
async def test_delete_payment_detail(client):
    response = await client.delete(
        f"/payment_details/?payment_id=3",
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "Payment detail has been deleted"

    response_check = await client.get(
        f"/payment_details/?payment_id=3",
    )
    assert response_check.status_code == 404
