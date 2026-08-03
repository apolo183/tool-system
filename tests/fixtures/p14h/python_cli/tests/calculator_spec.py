from src.calculator import increment


def test_increment() -> None:
    assert increment(1) == 2
