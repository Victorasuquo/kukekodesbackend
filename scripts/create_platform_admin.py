"""Create the first platform administrator.

Usage:
    python -m scripts.create_platform_admin admin@example.com 'StrongPass123' First Last
"""

import sys

from app.api.v1.auth.service import AuthService
from app.db.postgres import get_db_session


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("Usage: python -m scripts.create_platform_admin <email> <password> <first_name> <last_name>")

    email, password, first_name, last_name = sys.argv[1:5]
    db = get_db_session()
    try:
        user = AuthService.create_admin(
            db=db,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            by_admin_id="00000000-0000-0000-0000-000000000000",
        )
        print(f"Created platform admin {user.email} with learner ID {user.learner_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
