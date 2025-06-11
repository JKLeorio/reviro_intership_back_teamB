from datetime import date, datetime
from sqlalchemy import Column, Date, Integer, String, DateTime, ForeignKey, Enum
from typing import Optional
from sqlalchemy.orm import relationship, DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncAttrs
import sqlalchemy as sa
from .types import Gender, Role, Level
from utils.date_time_utils import get_current_time
from fastapi_users.db import SQLAlchemyBaseUserTable


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'users'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name : Mapped[str] = mapped_column(String, nullable=False)
    last_name : Mapped[str] = mapped_column(String, nullable=False)
    phone_number : Mapped[str] = mapped_column(String, unique=True, nullable=True)
    sex : Mapped[Gender] = mapped_column(Enum(Gender), nullable=True)
    birth_date : Mapped[date] = mapped_column(Date, nullable=True)
    role : Mapped[Role] = mapped_column(Enum(Role), default=Role.STUDENT)
    avatar_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_current_time)

    group_student = relationship("GroupStudent", back_populates="student", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="teacher")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Group(Base):
    __tablename__ = 'groups'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    course_id : Mapped[int] = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)

    course : Mapped["Course"] = relationship("Course", back_populates="groups")

    group_student : Mapped[list["GroupStudent"]] = relationship("GroupStudent", back_populates="group", cascade="all, delete-orphan")
    schedules : Mapped[list["Schedule"]] = relationship("Schedule", back_populates="group", cascade="all, delete-orphan")



class GroupStudent(Base):
    __tablename__ = 'group_students'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id : Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'), nullable=False)
    student_id : Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    group : Mapped["Group"] = relationship("Group", back_populates="group_student")
    student : Mapped["User"] = relationship("User", back_populates="group_student")


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)

class Payment(Base):
    __tablename__ = 'payments'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id : Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    amount : Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method_id : Mapped[int] = mapped_column(Integer, ForeignKey('payment_methods.id'), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)

    user : Mapped["User"] = relationship("User", back_populates="payments")
    payment_method : Mapped["PaymentMethod"] = relationship("PaymentMethod")



class Course(Base):
    __tablename__ = 'courses'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    price : Mapped[float] = mapped_column(Integer, nullable=False)
    level : Mapped[Level] = mapped_column(Enum(Level), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)

    groups : Mapped[list["Group"]] = relationship("Group", back_populates="course", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = 'subjects'
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    teacher_id : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)

    teacher : Mapped[Optional["User"]] = relationship("User", back_populates="subjects", foreign_keys=[teacher_id])
    lessons : Mapped[list["Lesson"]] = relationship("Lesson", back_populates="subject", cascade="all, delete-orphan")


class Classroom(Base):
    __tablename__ = 'classrooms'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    
    lessons : Mapped[list["Lesson"]] = relationship("Lesson", back_populates="classroom", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = 'schedules'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id : Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'), nullable=False)
    weekday : Mapped[int] = sa.Column(Integer, sa.CheckConstraint('weekday >= 0 AND weekday <= 6'), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)

    group : Mapped["Group"] = relationship("Group", back_populates="schedules")
    lesson_schedule : Mapped[list["LessonSchedule"]] = relationship("LessonSchedule", back_populates="schedule", cascade="all, delete-orphan")


class LessonSchedule(Base):
    __tablename__ = 'lesson_schedules'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lesson_id : Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'), nullable=False)
    schedule_id : Mapped[int] = mapped_column(Integer, ForeignKey('schedules.id'), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    
    lessons : Mapped["Lesson"] = relationship("Lesson", back_populates="lesson_schedule")
    schedule : Mapped["Schedule"] = relationship("Schedule", back_populates="lesson_schedule")


class Lesson(Base):
    __tablename__ = 'lessons'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)
    classroom_id : Mapped[int] = mapped_column(Integer, ForeignKey('classrooms.id'), nullable=False)
    lesson_start : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lesson_end : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subject_id : Mapped[int] = mapped_column(Integer, ForeignKey('subjects.id'), nullable=False)

    subject : Mapped["Subject"] = relationship("Subject", back_populates="lessons")
    lesson_schedule : Mapped["LessonSchedule"] = relationship("LessonSchedule", back_populates="lessons")
    classroom : Mapped["Classroom"] = relationship("Classroom", back_populates="lessons")
    homeworks : Mapped[list["Homework"]] = relationship("Homework", back_populates="lesson", cascade="all, delete-orphan")



class Homework(Base):
    __tablename__ = 'homeworks'
    
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lesson_id : Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'), nullable=False)
    due_time : Mapped[datetime] = mapped_column(DateTime, nullable=False)
    grade : Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime, default=get_current_time)

    lesson : Mapped["Lesson"] = relationship("Lesson", back_populates="homeworks")










