from sqladmin import ModelView
from models.course import Language, Level, Course

class LanguageAdmin(ModelView, model = Language):
    form_columns = [
        # Language.id,
        Language.name
    ]
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
    # from_widget_args = {
    #     'id' : {
    #         'readonly' : True
    #     },
        # 'created_at' : {
        #     'readonly' : True
        # }
    # }