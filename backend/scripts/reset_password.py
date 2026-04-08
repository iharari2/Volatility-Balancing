#!/usr/bin/env python3
"""
Admin CLI tool to reset a user's password directly against the database.

Usage:
    python scripts/reset_password.py --email user@example.com --password newpass

Requires SQL_URL environment variable pointing to the target database.
"""
import argparse
import os
import sys
from datetime import datetime, timezone

# Ensure backend root is on path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import bcrypt  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def reset_password(email: str, new_password: str, sql_url: str) -> None:
    if len(new_password) < 6:
        print("Error: password must be at least 6 characters.")
        sys.exit(1)

    engine = create_engine(sql_url)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email, tenant_id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if not row:
            print(f"Error: no user found with email '{email}'.")
            sys.exit(1)

        hashed = _hash_password(new_password)
        now = datetime.now(timezone.utc)

        conn.execute(
            text(
                "UPDATE users SET hashed_password = :pw, updated_at = :now WHERE email = :email"
            ),
            {"pw": hashed, "now": now, "email": email},
        )
        conn.commit()

    print(f"Password reset successfully for {email} (tenant: {row.tenant_id})")


def list_users(sql_url: str) -> None:
    engine = create_engine(sql_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT email, tenant_id, role, is_active, created_at FROM users ORDER BY created_at")
        ).fetchall()

    if not rows:
        print("No users found.")
        return

    print(f"\n{'Email':<40} {'Tenant':<20} {'Role':<10} {'Active':<8} {'Created'}")
    print("-" * 100)
    for r in rows:
        print(f"{r.email:<40} {r.tenant_id:<20} {r.role:<10} {str(r.is_active):<8} {r.created_at}")


def set_role(email: str, role: str, sql_url: str) -> None:
    valid_roles = ("owner", "trader")
    if role not in valid_roles:
        print(f"Error: role must be one of {valid_roles}.")
        sys.exit(1)

    engine = create_engine(sql_url)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email, tenant_id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if not row:
            print(f"Error: no user found with email '{email}'.")
            sys.exit(1)

        now = datetime.now(timezone.utc)
        conn.execute(
            text("UPDATE users SET role = :role, updated_at = :now WHERE email = :email"),
            {"role": role, "now": now, "email": email},
        )
        conn.commit()

    print(f"Role updated to '{role}' for {email} (tenant: {row.tenant_id})")


def main():
    parser = argparse.ArgumentParser(description="Admin password management tool")
    subparsers = parser.add_subparsers(dest="command")

    reset_parser = subparsers.add_parser("reset", help="Reset a user's password")
    reset_parser.add_argument("--email", required=True, help="User email")
    reset_parser.add_argument("--password", required=True, help="New password (min 6 chars)")

    role_parser = subparsers.add_parser("set-role", help="Set a user's role")
    role_parser.add_argument("--email", required=True, help="User email")
    role_parser.add_argument("--role", required=True, choices=["owner", "trader"], help="New role")

    subparsers.add_parser("list", help="List all users")

    args = parser.parse_args()

    sql_url = os.getenv("SQL_URL")
    if not sql_url:
        print("Error: SQL_URL environment variable is not set.")
        print("Example: $env:SQL_URL='postgresql://...'")
        sys.exit(1)

    if args.command == "reset":
        reset_password(args.email, args.password, sql_url)
    elif args.command == "set-role":
        set_role(args.email, args.role, sql_url)
    elif args.command == "list":
        list_users(sql_url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
