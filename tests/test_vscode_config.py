import os

def test_vscode_settings_exists():
    assert os.path.exists(".vscode/settings.json"), ".vscode/settings.json file is missing"

def test_vscode_settings_content():
    import json
    if not os.path.exists(".vscode/settings.json"):
        return
    with open(".vscode/settings.json", "r") as f:
        data = json.load(f)
    assert data.get("python.formatting.provider") == "black"
    assert data.get("editor.formatOnSave") is True
