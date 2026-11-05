import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import BackgroundTasks, HTTPException
from starlette.requests import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


API_DIR = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import auth  # noqa: E402
import models  # noqa: E402
import password_reset  # noqa: E402
import server  # noqa: E402


class PasswordResetApiTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(bind=engine)
        self.SessionFactory = sessionmaker(bind=engine)
        self.session = self.SessionFactory()
        self.user = models.User(
            email="ada@example.com",
            full_name="Ada Lovelace",
            hashed_password=auth.get_password_hash("old-password"),
        )
        self.session.add(self.user)
        self.session.commit()
        self.session.refresh(self.user)
        server.password_reset_request_limiter = (
            password_reset.PasswordResetRequestLimiter(
                per_ip_limit=100,
                global_limit=100,
                window_seconds=60,
            )
        )
        self.request_number = 0

    def tearDown(self):
        self.session.close()

    def request_reset(self, email="  ADA@example.com "):
        self.request_number += 1
        tasks = BackgroundTasks()
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/forgot-password",
                "headers": [],
                "client": (f"192.0.2.{self.request_number}", 1234),
            }
        )
        result = asyncio.run(
            server.forgot_password(
                server.ForgotPasswordRequest(email=email),
                tasks,
                request,
            )
        )
        return result, tasks

    def process_reset_request(self, email="ada@example.com"):
        sender = AsyncMock(return_value=True)
        asyncio.run(
            server.process_password_reset_request(
                email,
                db_factory=self.SessionFactory,
                send_email=sender,
            )
        )
        self.session.expire_all()
        return sender

    def test_forgot_password_is_private_and_persists_only_a_token_hash(self):
        existing, existing_tasks = self.request_reset()
        missing, missing_tasks = self.request_reset("missing@example.com")

        self.assertEqual(existing, missing)
        self.assertEqual(len(existing_tasks.tasks), 1)
        self.assertEqual(len(missing_tasks.tasks), 1)

        sender = self.process_reset_request()
        raw_token = sender.await_args.kwargs["reset_token"]
        record = self.session.query(models.PasswordResetToken).one()
        self.assertNotEqual(record.token_hash, raw_token)
        self.assertEqual(
            record.token_hash,
            password_reset.hash_password_reset_token(raw_token),
        )

    def test_account_cooldown_prevents_repeated_reset_emails(self):
        first_sender = self.process_reset_request()
        second_sender = self.process_reset_request()

        self.assertEqual(first_sender.await_count, 1)
        self.assertEqual(second_sender.await_count, 0)
        self.assertEqual(self.session.query(models.PasswordResetToken).count(), 1)

    def test_reset_consumes_link_and_invalidates_other_preissued_links(self):
        sender = self.process_reset_request()
        first_token = sender.await_args.kwargs["reset_token"]

        second_token = password_reset.generate_password_reset_token()
        self.session.add(
            models.PasswordResetToken(
                user_id=self.user.id,
                token_hash=password_reset.hash_password_reset_token(second_token),
                password_fingerprint=password_reset.password_fingerprint(
                    self.user.hashed_password
                ),
                expires_at=password_reset.password_reset_expiry(),
            )
        )
        self.session.commit()

        result = asyncio.run(
            server.reset_password(
                server.ResetPasswordRequest(
                    token=first_token,
                    new_password="new-password",
                ),
                self.session,
            )
        )

        self.assertEqual(result["message"], "Password updated successfully")
        self.assertTrue(auth.verify_password("new-password", self.user.hashed_password))

        for unusable_token in (first_token, second_token):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(
                    server.reset_password(
                        server.ResetPasswordRequest(
                            token=unusable_token,
                            new_password="another-password",
                        ),
                        self.session,
                    )
                )
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
