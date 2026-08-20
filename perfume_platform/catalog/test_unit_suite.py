"""Catalog positive + negative unit tests.
Pure helpers are tested directly; ORM-heavy paths are mocked."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase
from catalog.serializers import normalize_image_url, PerfumeSerializer, ProductSerializer, BulkBottleSerializer
from catalog.views import deduplicate_shop_products
from catalog.detail_utils import slugify_name, product_slug, product_url, split_notes, stock_state, _float, gallery_for, review_payload, card_payload, push_recently_viewed, recently_viewed, wishlist_ids, toggle_wishlist


class ImageNormalizationPositiveTests(SimpleTestCase):
    def test_http_preserved(self): self.assertEqual(normalize_image_url("http://x.test/a.jpg"),"http://x.test/a.jpg")
    def test_https_preserved(self): self.assertEqual(normalize_image_url("https://x.test/a.jpg"),"https://x.test/a.jpg")
    def test_data_url_preserved(self): self.assertEqual(normalize_image_url("data:image/png;base64,abc"),"data:image/png;base64,abc")
    def test_media_path_preserved(self): self.assertEqual(normalize_image_url("/media/perfumes/a.jpg"),"/media/perfumes/a.jpg")
    def test_media_without_leading_slash(self): self.assertEqual(normalize_image_url("media/perfumes/a.jpg"),"/media/perfumes/a.jpg")
    def test_perfumes_relative_path(self): self.assertEqual(normalize_image_url("perfumes/a.jpg"),"/media/perfumes/a.jpg")
    def test_bare_filename(self): self.assertEqual(normalize_image_url("a.jpg"),"/media/perfumes/a.jpg")
    def test_backslash_path_normalized(self): self.assertEqual(normalize_image_url("perfumes\\a.jpg"),"/media/perfumes/a.jpg")
    def test_windows_media_path_normalized(self): self.assertEqual(normalize_image_url("C:/site/media/perfumes/a.jpg"),"/media/perfumes/a.jpg")
    def test_spaces_trimmed(self): self.assertEqual(normalize_image_url("  /media/perfumes/a.jpg  "),"/media/perfumes/a.jpg")

class ImageNormalizationNegativeTests(SimpleTestCase):
    def test_none_is_empty(self): self.assertEqual(normalize_image_url(None),"")
    def test_empty_is_empty(self): self.assertEqual(normalize_image_url(""),"")
    def test_whitespace_is_empty(self): self.assertEqual(normalize_image_url("   "),"")
    def test_zero_is_path_not_crash(self): self.assertEqual(normalize_image_url(0),"/media/perfumes/0")
    def test_untrusted_relative_path_is_rooted(self): self.assertEqual(normalize_image_url("uploads/a.jpg"),"/uploads/a.jpg")
    def test_parent_path_does_not_crash(self): self.assertEqual(normalize_image_url("../a.jpg"),"/../a.jpg")

class CatalogHelperPositiveTests(SimpleTestCase):
    def test_slug_basic(self): self.assertEqual(slugify_name("Bleu de Chanel"),"bleu-de-chanel")
    def test_slug_punctuation(self): self.assertEqual(slugify_name("Dior Sauvage!"),"dior-sauvage")
    def test_slug_unicode_becomes_product(self): self.assertEqual(slugify_name("বাংলা"),"product")
    def test_slug_multiple_spaces(self): self.assertEqual(slugify_name("A   B"),"a-b")
    def test_split_comma(self): self.assertEqual(split_notes("Bergamot, Pepper"),["Bergamot","Pepper"])
    def test_split_middle_dot(self): self.assertEqual(split_notes("Bergamot · Pepper"),["Bergamot","Pepper"])
    def test_split_slash(self): self.assertEqual(split_notes("Bergamot/Pepper"),["Bergamot","Pepper"])
    def test_split_pipe(self): self.assertEqual(split_notes("Bergamot|Pepper"),["Bergamot","Pepper"])
    def test_split_mixed(self): self.assertEqual(split_notes("A, B · C/D|E"),["A","B","C","D","E"])
    def test_stock_zero(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=0)),("out_of_stock","Out of Stock"))
    def test_stock_negative(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=-1)),("out_of_stock","Out of Stock"))
    def test_stock_low(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=5)),("low_stock","Only 5 left"))
    def test_stock_high(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=6)),("in_stock","In Stock"))
    def test_float_decimal(self): self.assertEqual(_float(Decimal("10.50")),10.5)
    def test_float_int(self): self.assertEqual(_float(10),10.0)
    def test_float_none(self): self.assertIsNone(_float(None))

class CatalogHelperNegativeTests(SimpleTestCase):
    def test_slug_none_fallback(self): self.assertEqual(slugify_name(None),"product")
    def test_slug_empty_fallback(self): self.assertEqual(slugify_name(""),"product")
    def test_split_none_empty(self): self.assertEqual(split_notes(None),[])
    def test_split_empty_empty(self): self.assertEqual(split_notes(""),[])
    def test_split_only_delimiters_empty(self): self.assertEqual(split_notes(", · / |"),[])
    def test_stock_none_quantity_out(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=None)),("out_of_stock","Out of Stock"))

class ProductIdentityTests(SimpleTestCase):
    def product(self,name="Sauvage",brand="Dior",pid=7):
        b=SimpleNamespace(brand_name=brand); p=SimpleNamespace(perfume_name=name,brand=b,product_id=pid,perfume=SimpleNamespace(brand=b,perfume_name=name))
        p.perfume.perfume_id=11; p.perfume.brand_id=2
        return p
    def test_product_slug(self): self.assertEqual(product_slug(self.product()),"dior-sauvage")
    def test_product_url_contains_id(self): self.assertEqual(product_url(self.product()),"/product/dior-sauvage/7/")
    def test_product_slug_changes_with_brand(self): self.assertEqual(product_slug(self.product(brand="Tom Ford")),"tom-ford-sauvage")
    def test_product_url_format(self): self.assertTrue(product_url(self.product()).startswith("/product/"))

class GalleryTests(SimpleTestCase):
    def perfume(self,image): return SimpleNamespace(image_url=image)
    def test_gallery_has_main_image(self): self.assertEqual(gallery_for(self.perfume("/media/perfumes/a.jpg"))[0],"/media/perfumes/a.jpg")
    def test_gallery_has_four_images(self): self.assertEqual(len(gallery_for(self.perfume("/media/perfumes/a.jpg"))),4)
    def test_gallery_fallback_for_missing(self): self.assertTrue(gallery_for(self.perfume(None))[0].startswith("https://"))
    def test_gallery_main_not_duplicated(self):
        imgs=gallery_for(self.perfume("https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=900&q=80&auto=format")); self.assertEqual(len(imgs),4); self.assertEqual(len(imgs),len(set(imgs)))

class ReviewPayloadTests(SimpleTestCase):
    def review(self,first="John",last="Doe",comment="Nice",created=True):
        dt=__import__('datetime').datetime(2026,1,2,3,4,5) if created else None
        user=SimpleNamespace(first_name=first,last_name=last)
        return SimpleNamespace(review_id=3,rating=5,comment=comment,user=user,is_verified_purchase=1,created_at=dt)
    def test_review_id(self): self.assertEqual(review_payload(self.review())["review_id"],3)
    def test_review_name(self): self.assertEqual(review_payload(self.review())["user_name"],"John Doe")
    def test_review_comment(self): self.assertEqual(review_payload(self.review())["comment"],"Nice")
    def test_verified_bool(self): self.assertTrue(review_payload(self.review())["is_verified_purchase"])
    def test_date_iso_present(self): self.assertIn("2026-01-02",review_payload(self.review())["created_at"])
    def test_display_date_present(self): self.assertEqual(review_payload(self.review())["created_display"],"02 Jan 2026")
    def test_empty_names_use_verified_customer(self): self.assertEqual(review_payload(self.review("",""))["user_name"],"Verified Customer")
    def test_none_date_safe(self): self.assertIsNone(review_payload(self.review(created=False))["created_at"])
    def test_none_date_display_safe(self): self.assertEqual(review_payload(self.review(created=False))["created_display"],"")
    def test_none_comment_empty(self): self.assertEqual(review_payload(self.review(comment=None))["comment"],"")

class SerializerStructureTests(SimpleTestCase):
    def test_perfume_image_field_exists(self): self.assertIn("image_url",PerfumeSerializer().fields)
    def test_product_image_field_exists(self): self.assertIn("image_url",ProductSerializer().fields)
    def test_bulk_image_field_exists(self): self.assertIn("image_url",BulkBottleSerializer().fields)
    def test_perfume_brand_name_read_only(self): self.assertTrue(PerfumeSerializer().fields["brand_name"].read_only)
    def test_product_brand_name_read_only(self): self.assertTrue(ProductSerializer().fields["brand_name"].read_only)
    def test_product_image_is_method_field(self): self.assertEqual(ProductSerializer().fields["image_url"].__class__.__name__,"SerializerMethodField")
    def test_perfume_image_is_method_field(self): self.assertEqual(PerfumeSerializer().fields["image_url"].__class__.__name__,"SerializerMethodField")

class SessionListTests(SimpleTestCase):
    def request(self, values=None):
        class Session(dict):
            modified=False
        r=SimpleNamespace(session=Session(values or {})); return r
    def test_recent_inserted_front(self):
        r=self.request({"recently_viewed_products":[2,3]}); push_recently_viewed(r,7); self.assertEqual(r.session["recently_viewed_products"],[7,2,3])
    def test_recent_duplicate_moves_front(self):
        r=self.request({"recently_viewed_products":[7,2,3]}); push_recently_viewed(r,7); self.assertEqual(r.session["recently_viewed_products"],[7,2,3])
    def test_recent_limit_twelve(self):
        r=self.request({"recently_viewed_products":list(range(12))}); push_recently_viewed(r,99); self.assertEqual(len(r.session["recently_viewed_products"]),12)
    def test_recent_marks_modified(self):
        r=self.request(); push_recently_viewed(r,1); self.assertTrue(r.session.modified)
    def test_wishlist_empty(self): self.assertEqual(wishlist_ids(self.request()),[])
    def test_wishlist_toggle_add(self):
        r=self.request(); self.assertTrue(toggle_wishlist(r,5)); self.assertEqual(r.session["wishlist_products"],[5])
    def test_wishlist_toggle_remove(self):
        r=self.request({"wishlist_products":[5,6]}); self.assertFalse(toggle_wishlist(r,5)); self.assertEqual(r.session["wishlist_products"],[6])
    def test_wishlist_toggle_add_front(self):
        r=self.request({"wishlist_products":[6]}); self.assertTrue(toggle_wishlist(r,5)); self.assertEqual(r.session["wishlist_products"],[5,6])
    def test_wishlist_modified(self):
        r=self.request(); toggle_wishlist(r,5); self.assertTrue(r.session.modified)
    def test_wishlist_duplicate_remove_only_once(self):
        r=self.request({"wishlist_products":[5,5]}); self.assertFalse(toggle_wishlist(r,5)); self.assertEqual(r.session["wishlist_products"],[5])
    def test_recent_exclude_empty(self):
        r=self.request(); self.assertEqual(recently_viewed(r),[])

# Boundary tests for stock quantities

def _stock_test(qty, expected):
    def test(self): self.assertEqual(stock_state(SimpleNamespace(stock_quantity=qty))[0], expected)
    return test
for _q in range(0,21):
    setattr(CatalogHelperPositiveTests if _q else CatalogHelperNegativeTests, f"test_stock_boundary_{_q}", _stock_test(_q,"low_stock" if 1<=_q<=5 else "in_stock" if _q>=6 else "out_of_stock"))


class ShopDeduplicationTests(SimpleTestCase):
    def product(self, perfume_id, volume_ml, product_id):
        perfume = SimpleNamespace(perfume_id=perfume_id)
        return SimpleNamespace(
            perfume_id=perfume_id,
            perfume=perfume,
            volume_ml=Decimal(str(volume_ml)),
            product_id=product_id,
        )

    def test_5ml_and_10ml_same_perfume_show_once(self):
        products = [
            self.product(1, 5, 101),
            self.product(1, 10, 102),
        ]
        result = deduplicate_shop_products(products)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].product_id, 101)

    def test_multiple_variants_of_each_perfume_show_once(self):
        products = [
            self.product(1, 5, 101),
            self.product(1, 10, 102),
            self.product(1, 20, 103),
            self.product(2, 5, 201),
            self.product(2, 10, 202),
            self.product(3, 10, 301),
        ]
        result = deduplicate_shop_products(products)
        self.assertEqual([p.perfume_id for p in result], [1, 2, 3])

    def test_empty_shop_returns_empty(self):
        self.assertEqual(deduplicate_shop_products([]), [])
