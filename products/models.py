from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories"
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products_category"
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
      if not self.slug:
          base_slug = slugify(self.name)
          slug = base_slug
          counter = 1
          while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
              slug = f"{base_slug}-{counter}"
              counter += 1
          self.slug = slug
      super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "products_brand"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )

    sku = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    has_variants = models.BooleanField(default=False)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_product"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.base_price

    @property
    def is_on_sale(self):
        return bool(self.discount_price and self.discount_price < self.base_price)

    @property
    def discount_percentage(self):
        if self.is_on_sale:
            return round((1 - (self.discount_price / self.base_price)) * 100)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "products_product_image"
        ordering = ["display_order"]

    def __str__(self):
        return f"Image for {self.product.name}"


class Attribute(models.Model):
    """e.g. Color, Size"""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "products_attribute"

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    """e.g. Red, Large"""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=100)

    class Meta:
        db_table = "products_attribute_value"
        unique_together = ["attribute", "value"]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"



class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    attribute_values = models.ManyToManyField(AttributeValue, related_name="variants")

    sku = models.CharField(max_length=100, unique=True)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="products/variants/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "products_product_variant"

    def __str__(self):
        attrs = ", ".join(str(av) for av in self.attribute_values.all())
        return f"{self.product.name} ({attrs})"

    @property
    def price(self):
        return self.price_override if self.price_override else self.product.current_price

    @property
    def stock(self):
        """Convenience accessor — returns default warehouse StockItem for this variant."""
        from inventory.services import get_stock_for_variant
        return get_stock_for_variant(variant=self)
