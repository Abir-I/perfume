"""Accounts positive + negative unit tests.

All database-dependent serializer checks mock the User manager, so these tests
are deterministic and do not require the production MySQL database.
"""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from accounts.permissions import IsAdminRole, ADMIN_ROLE_ID
from accounts.serializers import RegisterSerializer


class AccountPermissionUnitTests(SimpleTestCase):
    def setUp(self):
        self.permission = IsAdminRole()

    def req(self, authenticated=True, role_id=1):
        return SimpleNamespace(user=SimpleNamespace(is_authenticated=authenticated, role_id=role_id))

    # Positive
    def test_admin_authenticated_allowed(self): self.assertTrue(self.permission.has_permission(self.req(True, 1), None))
    def test_admin_role_constant_is_one(self): self.assertEqual(ADMIN_ROLE_ID, 1)
    def test_truthy_authenticated_admin_allowed(self): self.assertTrue(self.permission.has_permission(self.req("yes", 1), None))
    def test_admin_role_zero_not_admin(self): self.assertFalse(self.permission.has_permission(self.req(True, 0), None))
    # Negative/security
    def test_unauthenticated_admin_denied(self): self.assertFalse(self.permission.has_permission(self.req(False, 1), None))
    def test_customer_denied(self): self.assertFalse(self.permission.has_permission(self.req(True, 2), None))
    def test_role_three_denied(self): self.assertFalse(self.permission.has_permission(self.req(True, 3), None))
    def test_missing_role_denied(self): self.assertFalse(self.permission.has_permission(SimpleNamespace(user=SimpleNamespace(is_authenticated=True)), None))
    def test_none_user_denied(self): self.assertFalse(self.permission.has_permission(SimpleNamespace(user=None), None))
    def test_missing_user_attribute_denied(self): self.assertFalse(self.permission.has_permission(SimpleNamespace(), None))
    def test_false_authenticated_denied(self): self.assertFalse(self.permission.has_permission(self.req(False, 1), None))
    def test_none_authenticated_denied(self): self.assertFalse(self.permission.has_permission(self.req(None, 1), None))
    def test_admin_string_role_denied(self): self.assertFalse(self.permission.has_permission(self.req(True, "1"), None))


class RegisterSerializerUnitTests(SimpleTestCase):
    def valid_data(self, **overrides):
        data = {"first_name":"Test","last_name":"Customer","email":"customer@example.com","password":"StrongPass123","phone":"01700000000"}
        data.update(overrides)
        return data

    def serializer(self, **overrides):
        s = RegisterSerializer(data=self.valid_data(**overrides))
        return s

    def assert_valid(self, **overrides):
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value = False
            s = self.serializer(**overrides)
            self.assertTrue(s.is_valid(), s.errors)
            return s

    def assert_invalid(self, **overrides):
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value = False
            s = self.serializer(**overrides)
            self.assertFalse(s.is_valid(), s.errors)
            return s

    # Positive validation
    def test_valid_registration(self): self.assert_valid()
    def test_eight_char_password_valid(self): self.assert_valid(password="12345678")
    def test_long_valid_password(self): self.assert_valid(password="A"*64)
    def test_optional_phone_absent_valid(self):
        data=self.valid_data(); data.pop("phone")
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value=False
            s=RegisterSerializer(data=data); self.assertTrue(s.is_valid(), s.errors)
    def test_email_case_shape_valid(self): self.assert_valid(email="user.name+tag@example.co.uk")
    def test_names_with_spaces_valid(self): self.assert_valid(first_name="Mary Jane", last_name="Doe Smith")
    def test_numeric_phone_text_valid(self): self.assert_valid(phone="8801700000000")
    def test_phone_at_max_length_valid(self): self.assert_valid(phone="1"*20)
    def test_first_name_at_max_length_valid(self): self.assert_valid(first_name="x"*100)
    def test_last_name_at_max_length_valid(self): self.assert_valid(last_name="x"*100)

    # Negative validation
    def test_missing_first_name_rejected(self):
        data=self.valid_data(); data.pop("first_name")
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value=False
            self.assertFalse(RegisterSerializer(data=data).is_valid())
    def test_missing_last_name_rejected(self):
        data=self.valid_data(); data.pop("last_name")
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value=False
            self.assertFalse(RegisterSerializer(data=data).is_valid())
    def test_missing_email_rejected(self): self.assert_invalid(email=None)
    def test_missing_password_rejected(self): self.assert_invalid(password=None)
    def test_blank_first_name_rejected(self): self.assert_invalid(first_name="")
    def test_blank_last_name_rejected(self): self.assert_invalid(last_name="")
    def test_blank_email_rejected(self): self.assert_invalid(email="")
    def test_blank_password_rejected(self): self.assert_invalid(password="")
    def test_short_password_7_rejected(self): self.assert_invalid(password="1234567")
    def test_short_password_1_rejected(self): self.assert_invalid(password="1")
    def test_invalid_email_rejected(self): self.assert_invalid(email="not-an-email")
    def test_invalid_email_no_domain_rejected(self): self.assert_invalid(email="user@")
    def test_invalid_email_no_at_rejected(self): self.assert_invalid(email="user.example.com")
    def test_first_name_101_rejected(self): self.assert_invalid(first_name="x"*101)
    def test_last_name_101_rejected(self): self.assert_invalid(last_name="x"*101)
    def test_phone_21_rejected(self): self.assert_invalid(phone="1"*21)
    def test_phone_100_rejected(self): self.assert_invalid(phone="1"*100)
    def test_duplicate_email_rejected(self):
        with patch("accounts.serializers.User.objects.filter") as f:
            f.return_value.exists.return_value=True
            s=self.serializer(); self.assertFalse(s.is_valid()); self.assertIn("email", s.errors)
    def test_password_integer_rejected(self): self.assert_invalid(password=12345678)
    def test_first_name_list_rejected(self): self.assert_invalid(first_name=["Test"])
    def test_email_list_rejected(self): self.assert_invalid(email=["x@y.com"])
    def test_phone_object_rejected(self): self.assert_invalid(phone={"value":"1"})

    def test_password_field_write_only(self): self.assertTrue(RegisterSerializer().fields["password"].write_only)
    def test_email_field_required(self): self.assertTrue(RegisterSerializer().fields["email"].required)
    def test_phone_field_optional(self): self.assertFalse(RegisterSerializer().fields["phone"].required)
    def test_first_name_max_length_100(self): self.assertEqual(RegisterSerializer().fields["first_name"].max_length,100)
    def test_last_name_max_length_100(self): self.assertEqual(RegisterSerializer().fields["last_name"].max_length,100)
    def test_phone_max_length_20(self): self.assertEqual(RegisterSerializer().fields["phone"].max_length,20)
    def test_password_min_length_8(self): self.assertEqual(RegisterSerializer().fields["password"].min_length,8)

    # Creation behavior is mocked, so no database is touched.
    def save_with(self, **overrides):
        fake_user=SimpleNamespace(user_id=77)
        with patch("accounts.serializers.User.objects.filter") as f, patch("accounts.serializers.User.objects.create", return_value=fake_user) as create:
            f.return_value.exists.return_value=False
            s=self.serializer(**overrides); self.assertTrue(s.is_valid(), s.errors); result=s.save()
            return result, create.call_args.kwargs

    def test_create_returns_user(self):
        result,_=self.save_with(); self.assertEqual(result.user_id,77)
    def test_create_hashes_password(self):
        _,kw=self.save_with(); self.assertNotEqual(kw["password_hash"],"StrongPass123"); self.assertTrue(kw["password_hash"].startswith("$2"))
    def test_create_customer_role(self): _,kw=self.save_with(); self.assertEqual(kw["role_id"],2)
    def test_create_active(self): _,kw=self.save_with(); self.assertEqual(kw["is_active"],1)
    def test_create_phone_preserved(self): _,kw=self.save_with(phone="01888888888"); self.assertEqual(kw["phone"],"01888888888")
    def test_create_missing_phone_defaults_empty(self):
        data=self.valid_data(); data.pop("phone")
        fake=SimpleNamespace(user_id=1)
        with patch("accounts.serializers.User.objects.filter") as f, patch("accounts.serializers.User.objects.create", return_value=fake) as create:
            f.return_value.exists.return_value=False; s=RegisterSerializer(data=data); self.assertTrue(s.is_valid()); s.save(); self.assertEqual(create.call_args.kwargs["phone"],"")
    def test_create_preserves_first_name(self): _,kw=self.save_with(first_name="Alice"); self.assertEqual(kw["first_name"],"Alice")
    def test_create_preserves_last_name(self): _,kw=self.save_with(last_name="Smith"); self.assertEqual(kw["last_name"],"Smith")
    def test_create_preserves_email(self): _,kw=self.save_with(email="a@b.com"); self.assertEqual(kw["email"],"a@b.com")

# Boundary-value positive tests

def _make_password_boundary_test(length):
    def test(self): self.assert_valid(password="P"*length)
    return test
for _n in (8,9,10,12,16,20,32,48,64,80):
    setattr(RegisterSerializerUnitTests, f"test_positive_password_length_{_n}", _make_password_boundary_test(_n))
