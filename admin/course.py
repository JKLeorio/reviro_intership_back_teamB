from sqladmin import ModelView
from models.course import Language, Level, Course

class LanguageAdmin(ModelView, model = Language):
    form_columns = [
        # Language.id,
        Language.name
    ]
    column_list = [
        Language.id,
        Language.name
    ]
    column_details_list = [
        Language.id,
        Language.name
    ]
    column_sortable_list = [Language.id]
    # from_widget_args = {
    #     'id' : {
    #         'readonly' : True
    #     },
    # }

class LevelAdmin(ModelView, model = Level):
    form_columns = [
        # Level.id,
        Level.code,
        Level.description
    ]
    column_list = [
        Level.id,
        Level.code,
        Level.description
    ]
    
    column_details_list = [
        Level.id,
        Level.code,
        Level.description
    ]

    column_sortable_list = [Level.id]
    # from_widget_args = {
    #     'id' : {
    #         'readonly' : True
    #     },
    # }

class CourseAdmin(ModelView, model = Course):
    form_columns = [
        # Course.id,
        Course.name,
        Course.price,
        Course.description,
        # Course.created_at,
        Course.language,
        Course.level,
    ]
    column_list = [
        Course.id,
        Course.name,
        Course.price,
        Course.description,
        Course.created_at,
        Course.language,
        Course.level
    ]

    column_details_list = [
        Course.id,
        Course.name,
        Course.price,
        Course.description,
        Course.created_at,
        Course.language,
        Course.level
    ]
    column_sortable_list = [Course.id]
    # from_widget_args = {
    #     'id' : {
    #         'readonly' : True
    #     },
        # 'created_at' : {
        #     'readonly' : True
        # }
    # }