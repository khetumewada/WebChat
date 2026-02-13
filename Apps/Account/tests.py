from unittest.mock import ANY, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SendOTPViewTests(TestCase):
    def test_returns_400_when_email_is_missing(self):
        response = self.client.post(reverse("Account:send_otp"), {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Email is required")

    def test_returns_400_when_email_already_registered(self):
        User.objects.create_user(
            username="khetu",
            email="khetu.mewada@gmail.com",
            password="StrongPass123!",
        )

        response = self.client.post(reverse("Account:send_otp"), {"email": "khetu.mewada@gmail.com"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Email already registered")

    @patch("Apps.Account.views.send_mail")
    @patch("Apps.Account.views.generate_otp", return_value=123456)
    def test_sends_otp_for_new_email(self, mock_generate_otp, mock_send_mail):
        response = self.client.post(reverse("Account:send_otp"), {"email": "khetu.mewada@gmail.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "OTP sent")
        mock_generate_otp.assert_called_once_with("khetu.mewada@gmail.com")
        mock_send_mail.assert_called_once_with(
            subject="Your OTP for Registration",
            message="Your OTP code is 123456. It will expire in 5 minutes.",
            from_email=ANY,
            recipient_list=["khetu.mewada@gmail.com"],
            fail_silently=False,
        )

    @patch("Apps.Account.views.send_mail")
    @patch("Apps.Account.views.generate_otp", return_value=123456)
    def test_sends_otp_normalizes_email_to_lowercase(self, mock_generate_otp, mock_send_mail):
        response = self.client.post(reverse("Account:send_otp"), {"email": "Khetu.Mewada@Gmail.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "OTP sent")
        mock_generate_otp.assert_called_once_with("khetu.mewada@gmail.com")
        mock_send_mail.assert_called_once()


class RegisterViewTests(TestCase):
    @patch("Apps.Account.views.send_welcome_register_email.delay")
    @patch("Apps.Account.views.clear_otp")
    @patch("Apps.Account.views.validate_otp", return_value=(True, None))
    def test_register_creates_user_and_redirects_to_login(
        self, mock_validate_otp, mock_clear_otp, mock_send_email
    ):
        payload = {
            "username": "khetu",
            "email": "khetu.mewada@gmail.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "otp": "123456",
        }

        response = self.client.post(reverse("Account:register"), payload)

        self.assertRedirects(response, reverse("Account:login"))
        self.assertTrue(User.objects.filter(email="khetu.mewada@gmail.com").exists())
        mock_validate_otp.assert_called_once_with("khetu.mewada@gmail.com", "123456")
        mock_clear_otp.assert_called_once_with("khetu.mewada@gmail.com")
        mock_send_email.assert_called_once_with("khetu.mewada@gmail.com")

    @patch("Apps.Account.views.send_welcome_register_email.delay")
    @patch("Apps.Account.views.clear_otp")
    @patch("Apps.Account.views.validate_otp", return_value=(False, "OTP expired or not sent"))
    def test_register_does_not_create_user_when_otp_invalid(
        self, mock_validate_otp, mock_clear_otp, mock_send_email
    ):
        payload = {
            "username": "khetu",
            "email": "khetu.mewada@gmail.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "otp": "000000",
        }

        response = self.client.post(reverse("Account:register"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="khetu.mewada@gmail.com").exists())
        mock_validate_otp.assert_called_once_with("khetu.mewada@gmail.com", "000000")
        self.assertIn("OTP expired or not sent", [str(m) for m in response.context["messages"]])
        mock_clear_otp.assert_not_called()
        mock_send_email.assert_not_called()

    def test_register_does_not_create_user_when_password_mismatch(self):
        payload = {
            "username": "khetu",
            "email": "khetu.mewada@gmail.com",
            "password": "StrongPass123!",
            "confirm_password": "WrongPass123!",
            "otp": "123456",
        }

        response = self.client.post(reverse("Account:register"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="khetu.mewada@gmail.com").exists())
        self.assertTrue(
            any("Passwords do not match" in err for err in response.context["form"].non_field_errors())
        )

    def test_register_does_not_create_user_when_username_exists(self):
        User.objects.create_user(
            username="khetu",
            email="khetu.mewada@gmail.com",
            password="StrongPass123!",
        )

        payload = {
            "username": "khetu",
            "email": "khetu.mewada135@gmail.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "otp": "123456",
        }

        response = self.client.post(reverse("Account:register"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="khetu").count(), 1)
        self.assertTrue(
            any("Username is already taken" in err for err in response.context["form"].errors["username"])
        )


class LoginViewTests(TestCase):
    @patch("Apps.Account.views.send_welcome_login_email.delay")
    def test_login_sets_access_and_refresh_cookies(self, mock_send_login_email):
        user = User.objects.create_user(
            username="khetu",
            email="khetu.mewada@gmail.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("Account:login"),
            {"username_or_email": "khetu", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("ChatApp:home"))
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
        mock_send_login_email.assert_called_once_with(user.email)

    def test_login_fail_wrong_password(self):
        User.objects.create_user(
            username="khetu",
            email="khetu.mewada@gmail.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("Account:login"),
            {"username_or_email": "khetu", "password": "WrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access", response.cookies)
        self.assertNotIn("refresh", response.cookies)
        self.assertTrue(
            any(
                "Invalid username/email or password" in err
                for err in response.context["form"].non_field_errors()
            )
        )

    def test_login_fail_user_not_exist(self):
        response = self.client.post(
            reverse("Account:login"),
            {"username_or_email": "khetu.mewada@gmail.com", "password": "StrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access", response.cookies)
        self.assertNotIn("refresh", response.cookies)
        self.assertTrue(
            any(
                "Invalid username/email or password" in err
                for err in response.context["form"].non_field_errors()
            )
        )
