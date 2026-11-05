import os
import unittest
from unittest.mock import AsyncMock, patch


class WelcomeEmailTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from api import email_service

        self.email_service = email_service

    def test_message_personalizes_welcome_without_password(self):
        message = self.email_service.build_welcome_message(
            full_name="Ada Lovelace",
            email="ada@example.com",
            frontend_url="https://fobsim-frontend.onrender.com/",
            sender="FobSim Research <research@example.com>",
        )

        self.assertEqual(message["to"], ["ada@example.com"])
        self.assertEqual(message["from"], "FobSim Research <research@example.com>")
        self.assertIn("Ada Lovelace", message["html"])
        self.assertIn("ada@example.com", message["html"])
        self.assertIn("https://fobsim-frontend.onrender.com/auth/login", message["html"])
        self.assertNotIn("password", message["html"].lower())

    def test_message_escapes_user_controlled_html(self):
        message = self.email_service.build_welcome_message(
            full_name='<script>alert("x")</script>',
            email="safe@example.com",
            frontend_url="https://fobsim.example",
            sender="FobSim <hello@example.com>",
        )

        self.assertNotIn("<script>", message["html"])
        self.assertIn("&lt;script&gt;", message["html"])

    async def test_send_uses_environment_configuration(self):
        send_async = AsyncMock(return_value={"id": "email_123"})
        env = {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM_EMAIL": "FobSim <hello@example.com>",
            "FRONTEND_URL": "https://fobsim.example/",
        }

        with patch.dict(os.environ, env, clear=True):
            sent = await self.email_service.send_welcome_email(
                full_name="Grace Hopper",
                email="grace@example.com",
                send_async=send_async,
            )

        self.assertTrue(sent)
        send_async.assert_awaited_once()
        payload = send_async.await_args.args[0]
        self.assertEqual(payload["to"], ["grace@example.com"])
        self.assertIn("Grace Hopper", payload["html"])

    async def test_send_failure_does_not_escape_to_signup(self):
        send_async = AsyncMock(side_effect=RuntimeError("provider unavailable"))
        env = {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM_EMAIL": "FobSim <hello@example.com>",
            "FRONTEND_URL": "https://fobsim.example",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertLogs("api.email_service", level="ERROR"):
                sent = await self.email_service.send_welcome_email(
                    full_name="Katherine Johnson",
                    email="katherine@example.com",
                    send_async=send_async,
                )

        self.assertFalse(sent)


class PasswordResetEmailTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from api import email_service

        self.email_service = email_service

    def test_message_contains_the_reset_link_and_not_the_password(self):
        message = self.email_service.build_password_reset_message(
            full_name="Ada Lovelace",
            email="ada@example.com",
            reset_token="signed-reset-token",
            frontend_url="https://fobsim.example/",
            sender="FobSim <hello@example.com>",
        )

        self.assertEqual(message["to"], ["ada@example.com"])
        self.assertIn(
            "https://fobsim.example/auth/reset-password#token=signed-reset-token",
            message["html"],
        )
        self.assertIn("30 minutes", message["html"])
        self.assertNotIn("current password", message["html"].lower())

    async def test_send_uses_resend_environment_configuration(self):
        send_async = AsyncMock(return_value={"id": "email_reset_123"})
        env = {
            "RESEND_API_KEY": "test_key",
            "RESEND_FROM_EMAIL": "FobSim <hello@example.com>",
            "FRONTEND_URL": "https://fobsim.example",
        }

        with patch.dict(os.environ, env, clear=True):
            sent = await self.email_service.send_password_reset_email(
                full_name="Ada Lovelace",
                email="ada@example.com",
                reset_token="signed-reset-token",
                send_async=send_async,
            )

        self.assertTrue(sent)
        payload = send_async.await_args.args[0]
        self.assertEqual(payload["subject"], "Reset your FobSim password")
        self.assertIn("signed-reset-token", payload["html"])


if __name__ == "__main__":
    unittest.main()
