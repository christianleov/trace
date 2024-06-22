import functools
import pathlib

import pytest
import requests

import db

TEST_USER_DATA = {"username": "test", "password": "123"}
PORT = 80
ROOT = f"http://localhost:{PORT}"


@functools.cache
def get_jwt_token():
    response = requests.post(f"{ROOT}/api/login", json=TEST_USER_DATA)
    print(response, response.text)
    token = response.json()["token"]
    headers = {"Authorization": "Bearer " + token}
    return headers


def prepare_db(register: bool = True):
    db.clean()
    db.create_database()
    if register:
        response = requests.post(f"{ROOT}/api/register", json=TEST_USER_DATA)
        assert response.status_code == 201


def get(url, *args, **kwargs):
    headers = get_jwt_token()
    response = requests.get(url, headers=headers)
    return response


def post(url, *args, **kwargs):
    headers = get_jwt_token()
    response = requests.post(url, headers=headers, *args, **kwargs)
    return response


def test_register():
    prepare_db(register=False)
    response = requests.post(f"{ROOT}/api/register", json=TEST_USER_DATA)
    assert response.status_code == 201


def test_login():
    prepare_db()
    response = post(f"{ROOT}/api/login", json=TEST_USER_DATA)
    assert response.status_code == 200


def test_upload_pdf():
    prepare_db()
    url = f"{ROOT}/api/pdfs"
    root = pathlib.Path("data/ebons/").expanduser()
    assert root.exists()

    for path in root.iterdir():
        print(f"Processing {path}")
        with open(path, "rb") as fd:
            files = {"file": fd}
            r = post(url, files=files)
            assert r.status_code == 200


def test_upload_image():
    return
    fpath = pathlib.Path(
        "./data/ocr_images/IMG-20230903-WA0007_6_lowqual.jpg"
    ).expanduser()
    assert fpath.exists()

    with open(fpath, "rb") as fd:
        files = {"file": fd}
        r = post(f"{ROOT}/api/images", files=files)
        assert r.status_code == 200


def test_bills():
    prepare_db()
    test_upload_pdf()
    response = get(f"{ROOT}/api/bills")
    assert response.status_code == 200


def test_charts_daily():
    prepare_db()
    response = get(f"{ROOT}/api/charts/daily")
    assert response.status_code == 200
    response = get(f"{ROOT}/api/charts/daily?month=6&year=2024")
    assert response.status_code == 200


def test_charts_monthly():
    prepare_db()
    response = get(f"{ROOT}/api/charts/monthly")
    assert response.status_code == 200
    response = get(f"{ROOT}/api/charts/monthly?year=2023")
    assert response.status_code == 200


def test_charts_yearly():
    prepare_db()
    response = get(f"{ROOT}/api/charts/yearly")
    assert response.status_code == 200
