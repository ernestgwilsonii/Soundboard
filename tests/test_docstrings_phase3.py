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


def get_function_docstrings(filepath):
    """
    Returns a dict of {func_name: docstring} for all functions in the file.
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    docs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docs[node.name] = ast.get_docstring(node)
    return docs


def test_socket_events_docstring():
    """
    Test that app/socket_events.py has a module-level docstring.
    """
    docstring = get_module_docstring("app/socket_events.py")
    assert (
        docstring is not None
    ), "app/socket_events.py is missing a module-level docstring"
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


@pytest.mark.parametrize(
    "filepath",
    [
        "app/main/routes.py",
        "app/auth/routes.py",
        "app/admin/routes.py",
        "app/soundboard/routes.py",
    ],
)
def test_routes_docstrings(filepath):
    """
    Test that route functions have docstrings.
    """
    # First check module docstring
    mod_doc = get_module_docstring(filepath)
    assert mod_doc is not None, f"{filepath} missing module docstring"

    # Check function docstrings
    func_docs = get_function_docstrings(filepath)
    for func_name, doc in func_docs.items():
        assert (
            doc is not None
        ), f"Function '{func_name}' in {filepath} is missing a docstring"


@pytest.mark.parametrize(
    "filepath", ["app/utils/audio.py", "app/utils/importer.py", "app/utils/packager.py"]
)
def test_utils_docstrings(filepath):
    """
    Test that utility functions and classes have docstrings.
    """
    # First check module docstring
    mod_doc = get_module_docstring(filepath)
    assert mod_doc is not None, f"{filepath} missing module docstring"

    # Check top-level function docstrings
    func_docs = get_function_docstrings(filepath)
    for func_name, doc in func_docs.items():
        assert (
            doc is not None
        ), f"Function '{func_name}' in {filepath} is missing a docstring"

    # Check class and method docstrings
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            assert (
                ast.get_docstring(node) is not None
            ), f"Class '{node.name}' in {filepath} is missing a docstring"
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Check if method has docstring
                    assert (
                        ast.get_docstring(item) is not None
                    ), f"Method '{node.name}.{item.name}' in {filepath} is missing a docstring"
