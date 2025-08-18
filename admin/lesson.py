from sqladmin import ModelView
from models.lesson import Attendance, Classroom



class ClassroomAdmin(ModelView, model=Classroom):
    column_sortable_list = [
        Classroom.id
    ]

    column_list = [
        Classroom.id,
        Classroom.name,
        Classroom.created_at
    ]

    column_details_list = [
        Classroom.id,
        Classroom.name,
        Classroom.created_at
    ]
    
    form_columns = [
        Classroom.name
    ]


class AttendanecAdmin(ModelView, model=Attendance):
    column_sortable_list = [
        Attendance.id
    ]

    column_list = [
        Attendance.id,
        Attendance.status,
        Attendance.created_at,
        Attendance.updated_at,
        Attendance.lesson,
        Attendance.student
    ]

    column_details_list = [
        Attendance.id,
        Attendance.status,
        Attendance.created_at,
        Attendance.updated_at,
        Attendance.lesson,
        Attendance.student
    ]
    
    form_columns = [
        Attendance.status,
        Attendance.student,
        Attendance.lesson
    ]

