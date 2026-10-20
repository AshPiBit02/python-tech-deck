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


def post(client,name="Temoit Huang",filename="cv.pdf",data=PDF,ctype="application/pdf"):
    return client.post("/apply",data={"name":name},files={"resumes":(filename,data,ctype)})

def test_valid_application(client):
    r=post(client)
    assert r.status_code==201
    records=client.get("/applications").json()
    assert records[0]["name"]=="Temoit Huang"
    assert (main.RESUME_DIR/records[0]["stored_filename"]).exists()


def test_rejects_non_pdf(client):
    assert post(client,filename="cv.docx",ctype="application/msword").status_code==415