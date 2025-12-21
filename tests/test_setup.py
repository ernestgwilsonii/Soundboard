import os

def test_requirements_file_exists():
    assert os.path.exists('requirements.txt')

def test_requirements_content():
    with open('requirements.txt', 'r') as f:
        content = f.read()
        assert 'Flask' in content
        assert 'Flask-WTF' in content
        assert 'python-dotenv' in content
        assert 'Werkzeug' in content

def test_directory_structure():
    assert os.path.exists('app')
    assert os.path.exists('static')
    assert os.path.exists('templates')
    assert os.path.isdir('app')
    assert os.path.isdir('static')
    assert os.path.isdir('templates')

def test_env_example_exists():
    assert os.path.exists('.env.example')

def test_env_example_content():
    with open('.env.example', 'r') as f:
        content = f.read()
        assert 'SECRET_KEY' in content
        assert 'DEBUG' in content
