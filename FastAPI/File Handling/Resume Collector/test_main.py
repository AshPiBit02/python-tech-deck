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


def post(client,id=536,name="Temoit Huang",filename="cv.pdf",data=PDF,ctype="application/pdf"):
    return client.post("/apply",data={"applicant_id":id,"name":name},files={"resumes":(filename,data,ctype)})

def test_valid_application(client):
    r=post(client)
    assert r.status_code==201
    records=client.get("/applications").json()
    assert records[0]["name"]=="Temoit Huang"
    assert (main.RESUME_DIR/records[0]["stored_filename"]).exists()


def test_rejects_non_pdf(client):
    assert post(client,filename="cv.docx",ctype="application/msword").status_code==415

def test_rejects_oversize(client):
    assert post(client,data=PDF+b"0"*(main.MAX_SIZE+1)).status_code==413

def test_rejects_fake_pdf(client):
    assert post(client, data=b"not a pdf at all").status_code == 415

def test_missing_name(client):
    r=client.post("/apply",data={"applicant_id":536},files={"resume":("cv.pdf",PDF,"application/pdf")})
    assert r.status_code==422
    
def test_applicant_id_saved(client):
    post(client, id=536)
    assert client.get("/applications").json()[0]["applicant_id"] == 536

def test_two_applicants_same_filename(client):
    post(client,name="Temoit Huang")
    post(client,name="Dikstra Troy")
    names=[r["stored_filename"] for r in client.get("/applications").json()]
    assert len(set(names))==2