import pytest
from agm import Roll, D

def test_the_D():
    assert D.min == 1
    assert D.max == 100
    assert D.num == 1

@pytest.mark.parametrize("test_input,expected", [
    (D[20], (1, 20, 1)),
    (D[6:15], (6, 15, 1)),
    (D[6:], (6, 20, 1)),
    (D[:10], (1, 10, 1)),
    (D[2::10], (1, 10, 2)),
    (D[2:5:8], (5, 8, 2)),
    pytest.param(D[2::], (1, 20, 2), marks = pytest.mark.xfail),
])
def test_roll_types(test_input: Roll, expected: tuple[int, int, int]):
    assert test_input.min == expected[0]
    assert test_input.max == expected[1]
    assert test_input.num == expected[2]

