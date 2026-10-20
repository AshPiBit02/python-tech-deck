import json
import pytest
from fastapi.testclient import TestClient

import main

PDF=b"%PDF-1.4\n%fake but valid header\n"

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,"RESUME_DIR",tmp_path/"resumes")
    monkeypatch.setattr(main,"DB_FILE",tmp_path/"applications.json")
    (tmp_path/"resumes").mkdir()
    return TestClient(main.app)
