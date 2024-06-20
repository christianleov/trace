import argparse
import hashlib
import os
import pathlib

import requests
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = (pathlib.Path(__file__).parent / "data").resolve()
EBON_DIR = DATA_DIR / "ebons"
USER_DATA = {
    "username": os.getenv("USER_NAME"),
    "password": os.getenv("USER_PASSWORD"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Read mails and extract attachments")
    parser.add_argument(
        "-s",
        "--server",
        type=str,
        default="https://rewe-app.yafa.app",
        help="Server URL",
    )
    parser.add_argument(
        "-r",
        "--reset-db",
        action="store_true",
        help="Reset database (only for localhost)",
    )
    args = parser.parse_args()
    return args


def login(server: str) -> str:
    response = requests.post(f"{server}/api/login", json=USER_DATA)
    assert response.status_code == 200
    token = response.json()["token"]
    headers = {"Authorization": "Bearer " + token}
    return headers


def reset_db(server: str):
    assert "localhost" in server
    import db

    print("Resetting database")
    db.clean()
    db.create_database()
    print(f"Creating user {USER_DATA['username']}")
    response = requests.post(f"{server}/api/register", json=USER_DATA)
    assert response.status_code == 201


def main():
    args = parse_args()
    if args.reset_db:
        reset_db(args.server)
    headers = login(args.server)
    response = requests.get(f"{args.server}/api/bills/hashes", headers=headers)
    assert response.status_code == 200
    hashes = response.json()

    stats_skipped = 0
    ebons = list(EBON_DIR.glob("REWE-eBon*pdf"))
    for file_path in ebons:
        with open(file_path, "rb") as fd:
            ebon = fd.read()
        file_hash = hashlib.sha256(ebon).hexdigest()
        if file_hash in hashes:
            stats_skipped += 1
            continue
        # The eBon does not exist on the server, so we upload it.
        with open(file_path, "rb") as fd:
            files = {"file": fd}
            response = requests.post(
                f"{args.server}/api/pdfs",
                files=files,
                headers=headers,
            )
            assert response.status_code == 200
        datetime_str = response.json()["datetime"]
        print(f"Uploaded bill from {datetime_str}")
    print(f"Skipped {stats_skipped} of {len(ebons)} eBons")


if __name__ == "__main__":
    main()
