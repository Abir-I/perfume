"""Order positive + negative unit tests.
The service's transaction wrapper is bypassed with __wrapped__ so these tests
exercise the transition logic without requiring a real database connection.
"""
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from orders.models import OrderStatus, PaymentStatus, ReturnStatus
from orders.services import ALLOWED_TRANSITIONS, advance_order_status
from orders.serializers import CheckoutSerializer


def service_without_db(order,new_status,changed_by=None,note=""):
    target=getattr(advance_order_status,"__wrapped__",advance_order_status)
    return target(order,new_status,changed_by,note)

class OrderEnumUnitTests(SimpleTestCase):
    def test_pending(self): self.assertEqual(OrderStatus.PENDING,"Pending")
    def test_confirmed(self): self.assertEqual(OrderStatus.CONFIRMED,"Confirmed")
    def test_processing(self): self.assertEqual(OrderStatus.PROCESSING,"Processing")
    def test_shipped(self): self.assertEqual(OrderStatus.SHIPPED,"Shipped")
    def test_delivered(self): self.assertEqual(OrderStatus.DELIVERED,"Delivered")
    def test_cancelled(self): self.assertEqual(OrderStatus.CANCELLED,"Cancelled")
    def test_payment_pending(self): self.assertEqual(PaymentStatus.PENDING,"Pending")
    def test_payment_completed(self): self.assertEqual(PaymentStatus.COMPLETED,"Completed")
    def test_payment_failed(self): self.assertEqual(PaymentStatus.FAILED,"Failed")
    def test_payment_refunded(self): self.assertEqual(PaymentStatus.REFUNDED,"Refunded")
    def test_return_pending(self): self.assertEqual(ReturnStatus.PENDING,"Pending")
    def test_return_approved(self): self.assertEqual(ReturnStatus.APPROVED,"Approved")
    def test_return_rejected(self): self.assertEqual(ReturnStatus.REJECTED,"Rejected")
    def test_return_received(self): self.assertEqual(ReturnStatus.RECEIVED,"Received")
    def test_return_refunded(self): self.assertEqual(ReturnStatus.REFUNDED,"Refunded")
    def test_return_cancelled(self): self.assertEqual(ReturnStatus.CANCELLED,"Cancelled")

class TransitionMatrixPositiveTests(SimpleTestCase):
    def test_pending_confirmed_allowed(self): self.assertIn(OrderStatus.CONFIRMED,ALLOWED_TRANSITIONS[OrderStatus.PENDING])
    def test_pending_cancelled_allowed(self): self.assertIn(OrderStatus.CANCELLED,ALLOWED_TRANSITIONS[OrderStatus.PENDING])
    def test_confirmed_processing_allowed(self): self.assertIn(OrderStatus.PROCESSING,ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED])
    def test_confirmed_cancelled_allowed(self): self.assertIn(OrderStatus.CANCELLED,ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED])
    def test_processing_shipped_allowed(self): self.assertIn(OrderStatus.SHIPPED,ALLOWED_TRANSITIONS[OrderStatus.PROCESSING])
    def test_shipped_delivered_allowed(self): self.assertIn(OrderStatus.DELIVERED,ALLOWED_TRANSITIONS[OrderStatus.SHIPPED])
    def test_delivered_terminal(self): self.assertEqual(ALLOWED_TRANSITIONS[OrderStatus.DELIVERED],set())
    def test_cancelled_terminal(self): self.assertEqual(ALLOWED_TRANSITIONS[OrderStatus.CANCELLED],set())
    def test_every_status_has_matrix_entry(self):
        for status in OrderStatus: self.assertIn(status,ALLOWED_TRANSITIONS)

class TransitionMatrixNegativeTests(SimpleTestCase):
    def test_pending_processing_blocked(self): self.assertNotIn(OrderStatus.PROCESSING,ALLOWED_TRANSITIONS[OrderStatus.PENDING])
    def test_pending_shipped_blocked(self): self.assertNotIn(OrderStatus.SHIPPED,ALLOWED_TRANSITIONS[OrderStatus.PENDING])
    def test_pending_delivered_blocked(self): self.assertNotIn(OrderStatus.DELIVERED,ALLOWED_TRANSITIONS[OrderStatus.PENDING])
    def test_confirmed_pending_blocked(self): self.assertNotIn(OrderStatus.PENDING,ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED])
    def test_confirmed_shipped_blocked(self): self.assertNotIn(OrderStatus.SHIPPED,ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED])
    def test_confirmed_delivered_blocked(self): self.assertNotIn(OrderStatus.DELIVERED,ALLOWED_TRANSITIONS[OrderStatus.CONFIRMED])
    def test_processing_confirmed_blocked(self): self.assertNotIn(OrderStatus.CONFIRMED,ALLOWED_TRANSITIONS[OrderStatus.PROCESSING])
    def test_processing_cancelled_blocked(self): self.assertNotIn(OrderStatus.CANCELLED,ALLOWED_TRANSITIONS[OrderStatus.PROCESSING])
    def test_processing_delivered_blocked(self): self.assertNotIn(OrderStatus.DELIVERED,ALLOWED_TRANSITIONS[OrderStatus.PROCESSING])
    def test_shipped_processing_blocked(self): self.assertNotIn(OrderStatus.PROCESSING,ALLOWED_TRANSITIONS[OrderStatus.SHIPPED])
    def test_shipped_cancelled_blocked(self): self.assertNotIn(OrderStatus.CANCELLED,ALLOWED_TRANSITIONS[OrderStatus.SHIPPED])
    def test_shipped_confirmed_blocked(self): self.assertNotIn(OrderStatus.CONFIRMED,ALLOWED_TRANSITIONS[OrderStatus.SHIPPED])
    def test_delivered_any_transition_blocked(self):
        for status in OrderStatus: self.assertNotIn(status,ALLOWED_TRANSITIONS[OrderStatus.DELIVERED])
    def test_cancelled_any_transition_blocked(self):
        for status in OrderStatus: self.assertNotIn(status,ALLOWED_TRANSITIONS[OrderStatus.CANCELLED])

class OrderServiceNegativeTests(SimpleTestCase):
    def order(self,status): return SimpleNamespace(status=status,save=MagicMock())
    def invalid(self,old,new):
        with self.assertRaises(ValidationError): service_without_db(self.order(old),new)
    def test_same_pending_invalid(self): self.invalid(OrderStatus.PENDING,OrderStatus.PENDING)
    def test_same_confirmed_invalid(self): self.invalid(OrderStatus.CONFIRMED,OrderStatus.CONFIRMED)
    def test_same_processing_invalid(self): self.invalid(OrderStatus.PROCESSING,OrderStatus.PROCESSING)
    def test_same_shipped_invalid(self): self.invalid(OrderStatus.SHIPPED,OrderStatus.SHIPPED)
    def test_same_delivered_invalid(self): self.invalid(OrderStatus.DELIVERED,OrderStatus.DELIVERED)
    def test_same_cancelled_invalid(self): self.invalid(OrderStatus.CANCELLED,OrderStatus.CANCELLED)
    def test_unknown_new_status(self): self.invalid(OrderStatus.PENDING,"Bogus")
    def test_pending_to_delivered(self): self.invalid(OrderStatus.PENDING,OrderStatus.DELIVERED)
    def test_pending_to_shipped(self): self.invalid(OrderStatus.PENDING,OrderStatus.SHIPPED)
    def test_confirmed_to_delivered(self): self.invalid(OrderStatus.CONFIRMED,OrderStatus.DELIVERED)
    def test_confirmed_to_shipped(self): self.invalid(OrderStatus.CONFIRMED,OrderStatus.SHIPPED)
    def test_processing_to_delivered(self): self.invalid(OrderStatus.PROCESSING,OrderStatus.DELIVERED)
    def test_processing_to_cancelled(self): self.invalid(OrderStatus.PROCESSING,OrderStatus.CANCELLED)
    def test_shipped_to_cancelled(self): self.invalid(OrderStatus.SHIPPED,OrderStatus.CANCELLED)
    def test_shipped_to_pending(self): self.invalid(OrderStatus.SHIPPED,OrderStatus.PENDING)
    def test_delivered_to_pending(self): self.invalid(OrderStatus.DELIVERED,OrderStatus.PENDING)
    def test_cancelled_to_pending(self): self.invalid(OrderStatus.CANCELLED,OrderStatus.PENDING)
    def test_invalid_string_from_confirmed(self): self.invalid(OrderStatus.CONFIRMED,"invalid")
    def test_invalid_string_from_processing(self): self.invalid(OrderStatus.PROCESSING,"invalid")
    def test_invalid_string_from_shipped(self): self.invalid(OrderStatus.SHIPPED,"invalid")
    def test_invalid_string_from_delivered(self): self.invalid(OrderStatus.DELIVERED,"invalid")
    def test_invalid_string_from_cancelled(self): self.invalid(OrderStatus.CANCELLED,"invalid")

class OrderServicePositiveTests(SimpleTestCase):
    def run_transition(self,old,new,changed_by=None,note=""):
        order=SimpleNamespace(status=old,save=MagicMock())
        empty_qs=MagicMock(); empty_qs.filter.return_value=[]
        with patch("orders.services.OrderItem.objects.select_related",return_value=empty_qs), patch("orders.services.Invoice.objects.filter",return_value=MagicMock()), patch("orders.services.Payment.objects.filter",return_value=MagicMock()), patch("orders.services.OrderStatusHistory.objects.create") as history:
            result=service_without_db(order,new,changed_by,note)
            self.assertEqual(result,new); self.assertEqual(order.status,new); order.save.assert_called_once_with(update_fields=["status"]); history.assert_called_once(); return history.call_args.kwargs
    def test_pending_confirmed(self): self.assertEqual(self.run_transition(OrderStatus.PENDING,OrderStatus.CONFIRMED)["status"],OrderStatus.CONFIRMED)
    def test_pending_cancelled(self): self.assertEqual(self.run_transition(OrderStatus.PENDING,OrderStatus.CANCELLED)["status"],OrderStatus.CANCELLED)
    def test_confirmed_processing(self): self.assertEqual(self.run_transition(OrderStatus.CONFIRMED,OrderStatus.PROCESSING)["status"],OrderStatus.PROCESSING)
    def test_confirmed_cancelled(self): self.assertEqual(self.run_transition(OrderStatus.CONFIRMED,OrderStatus.CANCELLED)["status"],OrderStatus.CANCELLED)
    def test_processing_shipped(self): self.assertEqual(self.run_transition(OrderStatus.PROCESSING,OrderStatus.SHIPPED)["status"],OrderStatus.SHIPPED)
    def test_shipped_delivered(self): self.assertEqual(self.run_transition(OrderStatus.SHIPPED,OrderStatus.DELIVERED)["status"],OrderStatus.DELIVERED)
    def test_changed_by_is_recorded(self):
        actor=SimpleNamespace(user_id=9); self.assertEqual(self.run_transition(OrderStatus.PENDING,OrderStatus.CONFIRMED,actor)["changed_by"],actor)
    def test_custom_note_is_recorded(self): self.assertEqual(self.run_transition(OrderStatus.PENDING,OrderStatus.CONFIRMED,note="Admin note")["note"],"Admin note")
    def test_default_note_is_generated(self): self.assertIn("Status changed from",self.run_transition(OrderStatus.PENDING,OrderStatus.CONFIRMED)["note"])
    def test_cancelled_updates_invoice(self):
        order=SimpleNamespace(status=OrderStatus.PENDING,save=MagicMock()); inv=MagicMock(); empty=MagicMock(); empty.filter.return_value=[]
        with patch("orders.services.OrderItem.objects.select_related",return_value=empty),patch("orders.services.Invoice.objects.filter",return_value=inv),patch("orders.services.OrderStatusHistory.objects.create"):
            service_without_db(order,OrderStatus.CANCELLED); inv.update.assert_called_once_with(status="Cancelled")
    def test_delivered_updates_payment(self):
        order=SimpleNamespace(status=OrderStatus.SHIPPED,save=MagicMock()); pay=MagicMock(); inv=MagicMock()
        with patch("orders.services.Payment.objects.filter",return_value=pay),patch("orders.services.Invoice.objects.filter",return_value=inv),patch("orders.services.OrderStatusHistory.objects.create"):
            service_without_db(order,OrderStatus.DELIVERED); pay.update.assert_called_once_with(status="Completed"); inv.update.assert_called_once_with(status="Paid")


class CheckoutSerializerPositiveTests(SimpleTestCase):
    def data(self, **overrides):
        d={"name":"Test Customer","email":"customer@example.com","phone":"01700000000","address":"1 Main Street","city":"Dhaka"}; d.update(overrides); return d
    def valid(self, **overrides):
        s=CheckoutSerializer(data=self.data(**overrides)); self.assertTrue(s.is_valid(),s.errors); return s
    def test_minimal_checkout_valid(self): self.valid()
    def test_cod_default_valid(self): self.assertEqual(self.valid().validated_data["payment_method"],"cod")
    def test_cod_explicit_valid(self): self.assertEqual(self.valid(payment_method="cod").validated_data["payment_method"],"cod")
    def test_cash_explicit_accepted_by_serializer(self): self.assertTrue(self.valid(payment_method="cash").is_valid())
    def test_cash_on_delivery_accepted_by_serializer(self): self.assertTrue(self.valid(payment_method="cash_on_delivery").is_valid())
    def test_optional_state_blank_valid(self): self.valid(state="")
    def test_optional_postal_blank_valid(self): self.valid(postal_code="")
    def test_optional_notes_blank_valid(self): self.valid(notes="")
    def test_custom_country_valid(self): self.valid(country="Bangladesh")
    def test_long_but_allowed_notes_valid(self): self.valid(notes="N"*2000)
    def test_name_max_length_valid(self): self.valid(name="N"*200)
    def test_address_max_length_valid(self): self.valid(address="A"*255)
    def test_city_max_length_valid(self): self.valid(city="C"*100)
    def test_phone_max_length_valid(self): self.valid(phone="1"*20)

class CheckoutSerializerNegativeTests(SimpleTestCase):
    def data(self, **overrides):
        d={"name":"Test Customer","email":"customer@example.com","phone":"01700000000","address":"1 Main Street","city":"Dhaka"}; d.update(overrides); return d
    def invalid(self, **overrides):
        s=CheckoutSerializer(data=self.data(**overrides)); self.assertFalse(s.is_valid()); return s
    def test_missing_name_rejected(self): self.invalid(name=None)
    def test_blank_name_rejected(self): self.invalid(name="")
    def test_missing_email_rejected(self): self.invalid(email=None)
    def test_invalid_email_rejected(self): self.invalid(email="not-email")
    def test_missing_phone_rejected(self): self.invalid(phone=None)
    def test_missing_address_rejected(self): self.invalid(address=None)
    def test_missing_city_rejected(self): self.invalid(city=None)
    def test_name_over_200_rejected(self): self.invalid(name="N"*201)
    def test_phone_over_20_rejected(self): self.invalid(phone="1"*21)
    def test_address_over_255_rejected(self): self.invalid(address="A"*256)
    def test_city_over_100_rejected(self): self.invalid(city="C"*101)
    def test_notes_over_2000_rejected(self): self.invalid(notes="N"*2001)
    def test_non_email_type_rejected(self): self.invalid(email=12345)
    def test_list_name_rejected(self): self.invalid(name=["x"])
    def test_list_phone_rejected(self): self.invalid(phone=["1"])
    def test_missing_required_fields_rejected(self):
        s=CheckoutSerializer(data={}); self.assertFalse(s.is_valid()); self.assertTrue(set(["name","email","phone","address","city"]).issubset(s.errors))
