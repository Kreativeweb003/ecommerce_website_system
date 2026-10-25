from django.db import transaction
from django.db.models import Q, Count, Max
from .models import Product, ProductImage, ProductVariant, Category, Brand
import logging
from PIL import Image

logger = logging.getLogger(__name__)


MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def validate_image_file(image_file):
    """Checks size and that the bytes really are an image (the browser's content type can be faked)."""
    if image_file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"{image_file.name} is larger than {MAX_IMAGE_SIZE_MB}MB.")
    try:
        img = Image.open(image_file)
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError("unsupported format")
        img.verify()
    except Exception:
        raise ValidationError(f"{image_file.name} is not a valid JPG, PNG, WebP or GIF image.")
    finally:
        image_file.seek(0)


@transaction.atomic
def add_product_image(*, product, image_file):
    validate_image_file(image_file)

    existing = product.images.all()
    is_first = not existing.exists()

    max_order = existing.aggregate(m=Max("display_order"))["m"]
    next_order = 0 if max_order is None else max_order + 1

    return ProductImage.objects.create(
        product=product,
        image=image_file,
        is_primary=is_first,
        display_order=next_order,
    )


@transaction.atomic
def set_primary_image(*, image):
    # The storefront shows images.first, which is ordered by display_order,
    # so "main" must also become display_order 0, not just flip a flag.
    others = list(image.product.images.exclude(pk=image.pk).order_by("display_order", "id"))
    image.is_primary = True
    image.display_order = 0
    for position, other in enumerate(others, start=1):
        other.is_primary = False
        other.display_order = position
    ProductImage.objects.bulk_update([image, *others], ["is_primary", "display_order"])


@transaction.atomic
def delete_product_image(*, image):
    product = image.product
    was_primary = image.is_primary
    storage, file_name = image.image.storage, image.image.name

    image.delete()

    if was_primary:
        replacement = product.images.order_by("display_order", "id").first()
        if replacement:
            replacement.is_primary = True
            replacement.save(update_fields=["is_primary"])

    def _remove_stored_file():
        # Runs only after the DB delete commits. A failure leaves an orphan file, never a broken row.
        if not file_name:
            return
        try:
            storage.delete(file_name)
        except Exception:
            logger.warning("Could not delete stored image %s", file_name, exc_info=True)

    transaction.on_commit(_remove_stored_file)


  


def get_published_products():
    return Product.objects.filter(status="published").select_related("category", "brand")


def get_featured_products(limit=8):
    return get_published_products().filter(is_featured=True)[:limit]


def get_product_by_slug(*, slug):
    return Product.objects.select_related("category", "brand").prefetch_related(
        "images", "variants__attribute_values__attribute"
    ).get(slug=slug, status="published")


def search_and_filter_products(*, filters):
    queryset = get_published_products()

    q = filters.get("q")
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q)
        )

    category = filters.get("category")
    if category:
        queryset = queryset.filter(category=category)

    brand = filters.get("brand")
    if brand:
        queryset = queryset.filter(brand=brand)

    min_price = filters.get("min_price")
    if min_price is not None:
        queryset = queryset.filter(base_price__gte=min_price)

    max_price = filters.get("max_price")
    if max_price is not None:
        queryset = queryset.filter(base_price__lte=max_price)

    sort = filters.get("sort")
    sort_map = {
        "newest": "-created_at",
        "price_asc": "base_price",
        "price_desc": "-base_price",
        "name": "name",
    }
    queryset = queryset.order_by(sort_map.get(sort, "-created_at"))

    return queryset


def get_related_products(*, product, limit=4):
    return get_published_products().filter(category=product.category).exclude(pk=product.pk)[:limit]


@transaction.atomic
def create_product(*, data, images=None):
    product = Product.objects.create(**data)

    if images:
        for order, image_file in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image_file,
                is_primary=(order == 0),
                display_order=order,
            )

    if not product.has_variants:
        from inventory.services import get_default_warehouse, get_or_create_stock_item
        warehouse = get_default_warehouse()
        if warehouse:
            get_or_create_stock_item(warehouse=warehouse, product=product)

    return product



@transaction.atomic
def update_product(*, product, data):
    from wishlist.services import check_and_notify_price_drop
  
    price_fields_changed = "base_price" in data or "discount_price" in data

    for field, value in data.items():
        setattr(product, field, value)
    product.save()

    if price_fields_changed and not product.has_variants:
        check_and_notify_price_drop(product=product)

    return product


def delete_product(*, product):
    product.delete()




def create_variant(*, product, data, attribute_value_ids):
    variant = ProductVariant.objects.create(product=product, **data)
    variant.attribute_values.set(attribute_value_ids)
    return variant


def get_categories_tree():
    return Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related("subcategories")


def get_all_brands():
    return Brand.objects.filter(is_active=True)


def get_all_products(*, status=None):
    """Admin-facing listing — includes draft/archived products, unlike get_published_products()."""
    queryset = Product.objects.select_related("category", "brand").order_by("-created_at")
    if status:
        queryset = queryset.filter(status=status)
    return queryset



def get_all_categories():
    """Admin listing, including inactive categories, with a product count per category."""
    return (
        Category.objects.select_related("parent")
        .annotate(product_count=Count("products", distinct=True))
        .order_by("name")
    )


def delete_category(*, category):
    if category.subcategories.exists():
        raise ValidationError("This category has subcategories. Move or delete them first.")
    category.delete()


def get_admin_brands():
    """Admin listing: includes inactive brands, with a product count per brand."""
    return Brand.objects.annotate(product_count=Count("products", distinct=True)).order_by("name")


def delete_brand(*, brand):
    # Product.brand uses SET_NULL, so products survive and simply lose their brand.
    brand.delete()




def _delete_stored_file(storage, file_name):
    try:
        storage.delete(file_name)
    except Exception:
        # An orphaned file is harmless; a failed request is not.
        logger.warning("Could not delete stored file %s", file_name, exc_info=True)


@transaction.atomic
def save_category(*, form, previous_image_name=""):
    """Saves the category form and, if the image was replaced, deletes the old stored file after commit."""
    category = form.save()
    if previous_image_name and category.image.name != previous_image_name:
        storage = category.image.storage
        transaction.on_commit(lambda: _delete_stored_file(storage, previous_image_name))
    return category


@transaction.atomic
def remove_category_image(*, category):
    file_name = category.image.name
    if not file_name:
        return
    storage = category.image.storage
    category.image = ""
    category.save(update_fields=["image"])
    transaction.on_commit(lambda: _delete_stored_file(storage, file_name))

















