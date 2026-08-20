"""Cart positive and negative unit tests; database lookups are mocked."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase
from accounts.models import Product
from cart.serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer

class AddCartItemValidationUnitTests(SimpleTestCase):
    def product(self, active=1): return SimpleNamespace(product_id=7,is_active=active)
    def validate(self,data,active=1):
        with patch("cart.serializers.Product.objects.get",return_value=self.product(active)):
            s=AddCartItemSerializer(data=data); return s,s.is_valid()
    # positive
    def test_default_quantity(self): s,ok=self.validate({"product_id":7}); self.assertTrue(ok,s.errors); self.assertEqual(s.validated_data["quantity"],1)
    def test_quantity_one(self): self.assertTrue(self.validate({"product_id":7,"quantity":1})[1])
    def test_quantity_two(self): self.assertTrue(self.validate({"product_id":7,"quantity":2})[1])
    def test_string_integer_coerced(self): s,ok=self.validate({"product_id":7,"quantity":"3"}); self.assertTrue(ok); self.assertEqual(s.validated_data["quantity"],3)
    def test_large_positive_quantity(self): self.assertTrue(self.validate({"product_id":7,"quantity":100})[1])
    def test_active_product_accepted(self): self.assertTrue(self.validate({"product_id":7,"quantity":1},1)[1])
    def test_get_product(self):
        product=self.product()
        with patch("cart.serializers.Product.objects.get",return_value=product):
            s=AddCartItemSerializer(data={"product_id":7,"quantity":1}); self.assertTrue(s.is_valid()); self.assertIs(s.get_product(),product)
    # negative
    def test_zero_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":0})[1])
    def test_negative_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":-1})[1])
    def test_large_negative_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":-100})[1])
    def test_decimal_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":2.5})[1])
    def test_decimal_string_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":"2.5"})[1])
    def test_alpha_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":"abc"})[1])
    def test_blank_quantity_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":""})[1])
    def test_missing_product_id_rejected(self): self.assertFalse(self.validate({"quantity":1})[1])
    def test_noninteger_product_id_rejected(self): self.assertFalse(self.validate({"product_id":"abc","quantity":1})[1])
    def test_zero_product_id_rejected_if_missing(self):
        with patch("cart.serializers.Product.objects.get",side_effect=Product.DoesNotExist): self.assertFalse(AddCartItemSerializer(data={"product_id":0,"quantity":1}).is_valid())
    def test_unknown_product_rejected(self):
        with patch("cart.serializers.Product.objects.get",side_effect=Product.DoesNotExist):
            s=AddCartItemSerializer(data={"product_id":7,"quantity":1}); self.assertFalse(s.is_valid()); self.assertIn("product_id",s.errors)
    def test_inactive_product_rejected(self): self.assertFalse(self.validate({"product_id":7,"quantity":1},0)[1])
    def test_error_zero_mentions_positive(self): s,ok=self.validate({"product_id":7,"quantity":0}); self.assertFalse(ok); self.assertIn("positive",str(s.errors["quantity"][0]))
    def test_error_inactive_mentions_available(self): s,ok=self.validate({"product_id":7,"quantity":1},0); self.assertFalse(ok); self.assertIn("available",str(s.errors["product_id"][0]))
    def test_quantity_field_default_one(self): self.assertEqual(AddCartItemSerializer().fields["quantity"].default,1)
    def test_product_id_required(self): self.assertTrue(AddCartItemSerializer().fields["product_id"].required)
    def test_quantity_integer_field(self): self.assertEqual(AddCartItemSerializer().fields["quantity"].__class__.__name__,"IntegerField")

class CartCalculationUnitTests(SimpleTestCase):
    def item(self,qty=2,price="10.50"): return SimpleNamespace(quantity=qty,product=SimpleNamespace(price=Decimal(price)))
    def test_subtotal_two_items(self): self.assertEqual(CartItemSerializer().get_subtotal(self.item()),Decimal("21.00"))
    def test_subtotal_one(self): self.assertEqual(CartItemSerializer().get_subtotal(self.item(1,"5")),Decimal("5.00"))
    def test_subtotal_zero(self): self.assertEqual(CartItemSerializer().get_subtotal(self.item(0,"5")),Decimal("0.00"))
    def test_subtotal_decimal_price(self): self.assertEqual(CartItemSerializer().get_subtotal(self.item(3,"0.10")),Decimal("0.30"))
    def test_subtotal_negative_quantity_math_is_deterministic(self): self.assertEqual(CartItemSerializer().get_subtotal(self.item(-1,"5")),Decimal("-5.00"))
    def test_empty_cart_total(self):
        cart=SimpleNamespace(cartitem_set=SimpleNamespace(select_related=lambda *a,**k: [])); self.assertEqual(CartSerializer().get_total(cart),Decimal("0.00"))
    def test_cart_total_multiple_items(self):
        items=[self.item(2,"10"),self.item(3,"5.50")]
        cart=SimpleNamespace(cartitem_set=SimpleNamespace(select_related=lambda *a,**k: items)); self.assertEqual(CartSerializer().get_total(cart),Decimal("36.50"))
    def test_cart_item_serializer_subtotal_field_exists(self): self.assertIn("subtotal",CartItemSerializer().fields)
    def test_cart_serializer_items_field_exists(self): self.assertIn("items",CartSerializer().fields)
    def test_cart_serializer_total_field_exists(self): self.assertIn("total",CartSerializer().fields)
    def test_product_mini_serializer_excludes_sensitive_fields(self):
        from cart.serializers import ProductMiniSerializer
        self.assertNotIn("password_hash",ProductMiniSerializer().fields)
    def test_cart_total_zero_price(self):
        cart=SimpleNamespace(cartitem_set=SimpleNamespace(select_related=lambda *a,**k:[self.item(5,"0")])); self.assertEqual(CartSerializer().get_total(cart),Decimal("0.00"))
    def test_cart_total_single_item(self):
        cart=SimpleNamespace(cartitem_set=SimpleNamespace(select_related=lambda *a,**k:[self.item(4,"2.25")])); self.assertEqual(CartSerializer().get_total(cart),Decimal("9.00"))

# Positive boundary tests 1..30

def _positive_qty(q):
    def test(self):
        product=SimpleNamespace(product_id=1,is_active=1)
        with patch("cart.serializers.Product.objects.get",return_value=product):
            s=AddCartItemSerializer(data={"product_id":1,"quantity":q}); self.assertTrue(s.is_valid(),s.errors); self.assertEqual(s.validated_data["quantity"],q)
    return test
for _q in range(1,31): setattr(AddCartItemValidationUnitTests,f"test_positive_quantity_{_q:02d}",_positive_qty(_q))

# Negative boundary tests for several invalid values

def _negative_qty(q):
    def test(self): self.assertFalse(self.validate({"product_id":7,"quantity":q})[1])
    return test
for _i,_q in enumerate(range(-1,-31,-1),1): setattr(AddCartItemValidationUnitTests,f"test_negative_quantity_{_i:02d}",_negative_qty(_q))
