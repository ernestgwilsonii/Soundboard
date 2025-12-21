import pytest
from app.models import User
from flask_login import UserMixin

def test_user_password_hashing():
    u = User(username='test', email='test@example.com')
    u.set_password('cat')
    assert not u.check_password('dog')
    assert u.check_password('cat')

def test_user_mixin_inheritance():
    u = User(username='test', email='test@example.com')
    assert isinstance(u, UserMixin)
    assert u.is_authenticated
    assert u.is_active
    assert not u.is_anonymous

def test_user_representation():
    u = User(username='test', email='test@example.com')
    assert str(u) == '<User test>'
