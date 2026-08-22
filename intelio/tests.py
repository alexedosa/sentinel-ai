from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Conversation, Message, UserSignal


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_token(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "alex",
                "password": "StrongPass123!",
                "email": "alex@test.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(username="alex").exists()
        )

        user = User.objects.get(username="alex")

        self.assertTrue(
            Token.objects.filter(user=user).exists()
        )

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="alex",
            password="StrongPass123!",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "alex",
                "password": "AnotherStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_login_returns_token(self):
        User.objects.create_user(
            username="alex",
            password="StrongPass123!",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "alex",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_invalid_login_is_rejected(self):
        User.objects.create_user(
            username="alex",
            password="StrongPass123!",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "alex",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)


class ConversationSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.alice = User.objects.create_user(
            username="alice",
            password="AlicePass123!",
        )

        self.bob = User.objects.create_user(
            username="bob",
            password="BobPass123!",
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(
            user=user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_user_can_create_conversation(self):
        self.authenticate(self.alice)

        response = self.client.post(
            "/api/mentor/conversations/",
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        conversation = Conversation.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            conversation.user,
            self.alice,
        )

    def test_user_can_read_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.alice
        )

        self.authenticate(self.alice)

        response = self.client.get(
            f"/api/mentor/conversations/{conversation.id}/"
        )

        self.assertEqual(response.status_code, 200)

    def test_user_cannot_read_another_users_conversation(self):
        conversation = Conversation.objects.create(
            user=self.alice
        )

        self.authenticate(self.bob)

        response = self.client.get(
            f"/api/mentor/conversations/{conversation.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_write_to_another_users_conversation(self):
        conversation = Conversation.objects.create(
            user=self.alice
        )

        self.authenticate(self.bob)

        response = self.client.post(
            f"/api/mentor/conversations/{conversation.id}/messages/",
            {
                "message": "I should not be able to write here.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            Message.objects.filter(
                conversation=conversation
            ).count(),
            0,
        )


class UserSignalSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.alice = User.objects.create_user(
            username="alice",
            password="AlicePass123!",
        )

        self.bob = User.objects.create_user(
            username="bob",
            password="BobPass123!",
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(
            user=user
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    @patch("intelio.views.analyze_evidence")
    @patch("intelio.views.build_evidence")
    @patch("intelio.views.build_context")
    @patch("intelio.views.sync_github")
    def test_signal_belongs_to_authenticated_user(
        self,
        mock_sync,
        mock_context,
        mock_build_evidence,
        mock_analyze,
    ):
        mock_sync.return_value = {
            "created": [],
            "skipped": [],
        }


        mock_context.return_value = {
            "github_activity": [],
            "user_signals": [],
            "current_projects": [],
            "code_evidence": [],
        }


        mock_build_evidence.return_value = {
            "user_request": "I am working on Sentinel authentication.",
            "github_evidence": [],
            "user_history": [],
            "project_state": [],
            "evidence_level": "none",
        }


        mock_analyze.return_value = {
            "activity": "development",
            "subject": "authentication",
            "project": "Sentinel",
            "status": "active",
            "intent_confidence": "high",
            "evidence_confidence": "low",
            "project_confidence": "high",
            "alignment": "insufficient_evidence",
            "evidence": "No external evidence available.",
            "recommendation": "Continue implementation.",
            "summary": "User is working on authentication.",
        }


        self.authenticate(self.alice)


        response = self.client.post(
            "/api/intelligence/",
            {
                "request": "I am working on Sentinel authentication."
            },
            format="json",
        )


        self.assertEqual(response.status_code, 200)


        signal = UserSignal.objects.get(
            id=response.data["signal_id"]
        )


        self.assertEqual(
            signal.user,
            self.alice,
        )


        mock_sync.assert_called_once()
        mock_context.assert_called_once_with(
            user=self.alice
        )

    def test_users_cannot_see_each_others_signals(self):
        UserSignal.objects.create(
            user=self.alice,
            request="Alice private development intention.",
        )

        UserSignal.objects.create(
            user=self.bob,
            request="Bob private development intention.",
        )

        from intelio.services.context import build_context

        alice_context = build_context(
            user=self.alice
        )

        bob_context = build_context(
            user=self.bob
        )

        alice_signals = [
            signal["request"]
            for signal in alice_context["user_signals"]
        ]

        bob_signals = [
            signal["request"]
            for signal in bob_context["user_signals"]
        ]

        self.assertIn(
            "Alice private development intention.",
            alice_signals,
        )

        self.assertNotIn(
            "Bob private development intention.",
            alice_signals,
        )

        self.assertIn(
            "Bob private development intention.",
            bob_signals,
        )

        self.assertNotIn(
            "Alice private development intention.",
            bob_signals,
        )
