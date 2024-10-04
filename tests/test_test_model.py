import pytest
from models.test_model import TestModel

def test_add_test():
    model = TestModel()
    model.add_test('Test 1')
    assert 'Test 1' in model.tests

def test_remove_test():
    model = TestModel()
    model.add_test('Test 1')
    model.remove_test('Test 1')
    assert 'Test 1' not in model.tests