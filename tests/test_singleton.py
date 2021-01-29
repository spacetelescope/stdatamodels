"""Test SingletonList"""
import copy

from stdatamodels.model_base import SingletonList


def test_copy():
    """Test that copying returns the same list"""
    singleton = SingletonList()
    s_copy = copy.copy(singleton)
    assert id(singleton) == id(s_copy)


def test_deepcopy():
    """Test that deep copying returns the same list"""
    singleton = SingletonList()
    s_copy = copy.deepcopy(singleton)
    assert id(singleton) == id(s_copy)
