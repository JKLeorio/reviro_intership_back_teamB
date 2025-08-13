from sqladmin import ModelView
from models import Group


class GroupAdmin(ModelView, model = Group):
    column_list = [
        Group.id,
        Group.name,
        Group.created_at,
        Group.start_date,
        Group.approximate_lesson_start,
        Group.end_date,
        Group.is_active,
        Group.is_archived,
        Group.course,
        Group.teacher,
    ]
    form_columns = [
        # Group.id,
        Group.name,
        # Group.created_at,
        Group.start_date,
        Group.approximate_lesson_start,
        Group.end_date,
        Group.is_active,
        Group.is_archived,
        Group.course,
        Group.teacher,
    ]
    # from_widget_args = {
    #     'id' : {
    #         'readonly' : True
    #     },
    #     'created_at' : {
    #         'readonly' : True
    #     }
    # }