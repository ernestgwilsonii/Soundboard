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
