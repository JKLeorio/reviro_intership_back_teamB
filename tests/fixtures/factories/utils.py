from enum import Enum
import random

def get_enum_randomizer(enum_cls: Enum):
    def get_random_attr():
        return random.choice(list(enum_cls))
    return get_random_attr