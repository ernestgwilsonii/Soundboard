import ast
import os
import pytest

def get_module_docstring(filepath):
    """
    Reads a file and returns its module-level docstring using ast.
    """
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    return ast.get_docstring(tree)

def test_socket_events_docstring():
    """
    Test that app/socket_events.py has a module-level docstring.
    """
    docstring = get_module_docstring("app/socket_events.py")
    assert docstring is not None, "app/socket_events.py is missing a module-level docstring"
    assert len(docstring.strip()) > 0, "app/socket_events.py docstring is empty"

def test_init_docstring():
    """
    Test that app/__init__.py has a module-level docstring.
    """
    docstring = get_module_docstring("app/__init__.py")
    assert docstring is not None, "app/__init__.py is missing a module-level docstring"

def test_soundboard_docstring():
    """
    Test that soundboard.py has a module-level docstring.
    """
    docstring = get_module_docstring("soundboard.py")
    assert docstring is not None, "soundboard.py is missing a module-level docstring"
