from django.db import transaction
from django.db.models import Q, Count
from .models import Product, ProductImage, ProductVariant, Category, Brand


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


def add_product_image(*, product, image_file, is_primary=False):
    if is_primary:
        ProductImage.objects.filter(product=product).update(is_primary=False)
    return ProductImage.objects.create(product=product, image=image_file, is_primary=is_primary)


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




