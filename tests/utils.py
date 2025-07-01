from typing import Dict, Type

def dict_comparator(expected: Dict[str, Type], received: Dict[str, Type]) -> None:
    for key, elem in expected.items():
        rec_value = received.get(key, None)
        if not rec_value:
            raise AssertionError
        assert rec_value == elem
    