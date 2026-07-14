#!/usr/bin/env python3
"""Seed the attendance server with sample data for manual GUI exploration.

Precondition: the Flask server must already be running
(`python -m server.app`, or via `./run.sh`).

Usage:
    python scripts/seed_mock_data.py [--count N]

Creates N instructor accounts (default 1), each with one sample class and
roster, reusing the same fixtures the automated tests use
(tests/mock_data.py) so manual exploration and CI stay consistent.

Exit codes: 0 on success, 1 if the server can't be reached or a request
fails for a reason other than "already exists" (which is treated as OK,
so the script is safe to re-run).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api_client import ApiClient, ApiError
from tests.mock_data import SAMPLE_INSTRUCTOR, sample_class_payload


def seed_one(client: ApiClient, index: int) -> None:
    email = SAMPLE_INSTRUCTOR["email"] if index == 0 else f"instructor{index}@example.edu"
    account_payload = {**SAMPLE_INSTRUCTOR, "email": email}

    try:
        account = client.create_account(account_payload)
        print(f"Created instructor {email} ({account['user_id']})")
    except ApiError as e:
        if e.status_code == 409:
            print(f"Instructor {email} already exists, authenticating instead.")
            account = client.authenticate(email, account_payload["password"])
        else:
            raise

    class_code = "COMP101" if index == 0 else f"COMP10{index + 1}"
    try:
        created_class = client.create_class(
            sample_class_payload(account["user_id"], class_code=class_code)
        )
        print(f"  Created class {created_class['class_code']} ({created_class['class_id']})")
    except ApiError as e:
        if e.status_code == 409:
            print(f"  Class {class_code} already exists for this instructor, skipping.")
        else:
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1, help="Number of sample instructors to create")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    args = parser.parse_args()

    client = ApiClient(base_url=args.base_url)
    try:
        for i in range(args.count):
            seed_one(client, i)
    except ApiError as e:
        print(f"Failed to seed mock data: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nDone. Log in with:")
    print(f"  email:    {SAMPLE_INSTRUCTOR['email']}")
    print(f"  password: {SAMPLE_INSTRUCTOR['password']}")


if __name__ == "__main__":
    main()
