from factory import Factory, Faker

from db.types import Role


class StudentRegisterDataFactory(Factory):
    class Meta:
        model = dict
    
    # first_name = Faker('name')
    # last_name = Faker('name')
    full_name = Faker('name')
    email = Faker('email')
    phone_number = Faker('phone_number')
    role = Role.STUDENT
    
class TeacherRegisterDataFactory(Factory):
    class Meta:
        model = dict
    
    # first_name = Faker('name')
    # last_name = Faker('name')
    full_name = Faker('name')
    email = Faker('email')
    phone_number = Faker('phone_number')
    # description = Faker('paragraph')
    role = Role.TEACHER
