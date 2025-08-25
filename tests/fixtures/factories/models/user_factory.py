from schemas.user import UserResponse
from tests.fixtures.factories.models.factory import CustomFactoryBase
import factory

from tests.fixtures.factories.utils import get_enum_randomizer
from db.types import Role
from models.user import User


role_randomizer = get_enum_randomizer(Role)

class UserFactory(CustomFactoryBase):
    class _Config:
        factory_model = User
        factory_model_schema = UserResponse
        unique = ('email', 'phone_number')

    first_name = factory.Faker('name')
    last_name = factory.Faker('name')
    email = factory.Faker('email')
    phone_number = factory.Faker('phone_number')
    role = factory.LazyFunction(role_randomizer)
    hashed_password = factory.Faker('sha256')
    # is_verified = factory.Faker('pybool')
    # is_active = factory.Faker('pybool')
    is_verified = True
    is_active = True
    description = factory.Faker("paragraph")


