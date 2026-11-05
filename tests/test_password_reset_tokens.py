import importlib
import unittest


class PasswordResetTokenTests(unittest.TestCase):
    def setUp(self):
        self.tokens = importlib.import_module("api.password_reset")

    def test_generated_token_is_opaque_and_only_its_hash_is_stored(self):
        token = self.tokens.generate_password_reset_token()
        token_hash = self.tokens.hash_password_reset_token(token)

        self.assertGreaterEqual(len(token), 40)
        self.assertNotIn(".", token)
        self.assertNotEqual(token_hash, token)
        self.assertEqual(len(token_hash), 64)
        self.assertEqual(
            self.tokens.hash_password_reset_token(token),
            token_hash,
        )

    def test_password_fingerprint_changes_when_password_changes(self):
        old_fingerprint = self.tokens.password_fingerprint("old-password-hash")
        new_fingerprint = self.tokens.password_fingerprint("new-password-hash")

        self.assertNotEqual(old_fingerprint, new_fingerprint)

    def test_request_limiter_blocks_ip_and_global_bursts(self):
        limiter = self.tokens.PasswordResetRequestLimiter(
            per_ip_limit=2,
            global_limit=3,
            window_seconds=60,
        )

        self.assertTrue(limiter.allow("192.0.2.1", now=100))
        self.assertTrue(limiter.allow("192.0.2.1", now=101))
        self.assertFalse(limiter.allow("192.0.2.1", now=102))
        self.assertTrue(limiter.allow("192.0.2.2", now=103))
        self.assertFalse(limiter.allow("192.0.2.3", now=104))
        self.assertTrue(limiter.allow("192.0.2.1", now=161))


if __name__ == "__main__":
    unittest.main()
