from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from reviews.services import get_approved_reviews_for_product, get_product_rating_summary, get_existing_review
from core.permissions import superuser_required
from django.core.exceptions import ValidationError

from . import services
from .forms import ProductForm, ProductImageForm, ProductFilterForm, ProductVariantForm, CategoryForm, BrandForm
from core.templatetags.cloudinary_extras import optimized
from .models import Product, Category, Brand, ProductImage

from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST











def home_view(request):
    featured_products = services.get_featured_products()
    categories = services.get_categories_tree()
    return render(request, "products/home.html", {
        "featured_products": featured_products,
        "categories": categories,
    })


def product_list_view(request):
    form = ProductFilterForm(request.GET or None)
    filters = {}
    if form.is_valid():
        filters = form.cleaned_data

    products = services.search_and_filter_products(filters=filters)

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "products/product_list.html", {
        "page_obj": page_obj,
        "form": form,
        "categories": services.get_categories_tree(),
        "brands": services.get_all_brands(),
    })




def product_detail_view(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "brand"), slug=slug, status="published")
    related_products = services.get_related_products(product=product)

    reviews = get_approved_reviews_for_product(product=product)
    rating_summary = get_product_rating_summary(product=product)

    user_review = None
    if request.user.is_authenticated:
        user_review = get_existing_review(product=product, user=request.user)

    return render(request, "products/product_detail.html", {
        "product": product,
        "images": product.images.all(),
        "variants": product.variants.filter(is_active=True),
        "related_products": related_products,
        "reviews": reviews,
        "rating_summary": rating_summary,
        "user_review": user_review,
    })

  

def category_view(request, slug):
    from .models import Category
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = services.get_published_products().filter(category=category)

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "products/category.html", {
        "category": category,
        "page_obj": page_obj,
    })


# --- Seller/Admin management views ---


@login_required
@superuser_required
def admin_product_list_view(request):
    status = request.GET.get("status")
    products = services.get_all_products(status=status)

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "products/admin_product_list.html", {
        "page_obj": page_obj,
        "status": status,
    })


@login_required
@superuser_required
def product_create_view(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            images = request.FILES.getlist("images")
            try:
                for image_file in images:
                    services.validate_image_file(image_file)
            except ValidationError as e:
                form.add_error(None, e.messages[0])
            else:
                services.create_product(data=form.cleaned_data, images=images)
                messages.success(request, "Product created successfully.")
                return redirect("products:admin_product_list")
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def product_update_view(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            services.update_product(product=product, data=form.cleaned_data)
            messages.success(request, "Product updated successfully.")
            return redirect("products:admin_product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_form.html", {"form": form, "action": "Edit", "product": product})


@login_required
@superuser_required
def product_delete_view(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        services.delete_product(product=product)
        messages.success(request, "Product deleted.")
        return redirect("products:product_list")

    return render(request, "products/product_confirm_delete.html", {"product": product})


@login_required
@superuser_required
def variant_create_view(request, slug):
    from inventory.services import get_default_warehouse, get_or_create_stock_item

    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        form = ProductVariantForm(request.POST, request.FILES)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            form.save_m2m()

            warehouse = get_default_warehouse()
            if warehouse:
                get_or_create_stock_item(warehouse=warehouse, variant=variant)

            messages.success(request, "Variant added successfully.")
            return redirect("products:product_detail", slug=product.slug)
    else:
        form = ProductVariantForm()

    return render(request, "products/variant_form.html", {"form": form, "product": product})



@login_required
@superuser_required
def admin_category_list_view(request):
    categories = services.get_all_categories()
    return render(request, "products/admin_category_list.html", {"categories": categories})


@login_required
@superuser_required
def admin_category_create_view(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            return redirect("products:admin_category_list")
    else:
        form = CategoryForm()

    return render(request, "products/admin_category_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def admin_category_update_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    previous_image_name = category.image.name
    saved_image_url = optimized(category.image, "q_auto,f_auto,w_400,h_400,c_fill")  # "" if no image

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            services.save_category(form=form, previous_image_name=previous_image_name)
            messages.success(request, "Category updated.")
            return redirect("products:admin_category_list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "products/admin_category_form.html", {
        "form": form, "action": "Edit", "category": category, "saved_image_url": saved_image_url,
    })


@login_required
@superuser_required
def admin_category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        try:
            services.delete_category(category=category)
            messages.success(request, "Category deleted.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, "message") else e))
        return redirect("products:admin_category_list")

    return render(request, "products/admin_category_confirm_delete.html", {
        "category": category,
        "product_count": category.products.count(),
        "subcategory_count": category.subcategories.count(),
    })

@login_required
@superuser_required
def admin_brand_list_view(request):
    brands = services.get_admin_brands()
    return render(request, "products/admin_brand_list.html", {"brands": brands})


@login_required
@superuser_required
def admin_brand_create_view(request):
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand created.")
            return redirect("products:admin_brand_list")
    else:
        form = BrandForm()

    return render(request, "products/admin_brand_form.html", {"form": form, "action": "Create"})


@login_required
@superuser_required
def admin_brand_update_view(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand updated.")
            return redirect("products:admin_brand_list")
    else:
        form = BrandForm(instance=brand)

    return render(request, "products/admin_brand_form.html", {"form": form, "action": "Edit", "brand": brand})


@login_required
@superuser_required
def admin_brand_delete_view(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == "POST":
        services.delete_brand(brand=brand)
        messages.success(request, "Brand deleted.")
        return redirect("products:admin_brand_list")

    return render(request, "products/admin_brand_confirm_delete.html", {
        "brand": brand,
        "product_count": brand.products.count(),
    })



def _image_json(image):
    return {
        "id": image.pk,
        "thumb_url": optimized(image.image, "q_auto,f_auto,w_300,h_300,c_fill"),
        "is_primary": image.is_primary,
        "delete_url": reverse("products:admin_product_image_delete", args=[image.pk]),
        "primary_url": reverse("products:admin_product_image_primary", args=[image.pk]),
    }


@login_required
@superuser_required
@require_POST
def admin_product_image_add_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    files = request.FILES.getlist("images")
    if not files:
        return JsonResponse({"success": False, "error": "No image received."}, status=400)

    added, errors = [], []
    for image_file in files:
        try:
            added.append(_image_json(services.add_product_image(product=product, image_file=image_file)))
        except ValidationError as e:
            errors.append(e.messages[0])

    return JsonResponse({"success": bool(added), "images": added, "errors": errors}, status=200 if added else 400)


@login_required
@superuser_required
@require_POST
def admin_product_image_delete_view(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product = image.product
    services.delete_product_image(image=image)
    new_primary = product.images.filter(is_primary=True).first()
    return JsonResponse({"success": True, "primary_id": new_primary.pk if new_primary else None})


@login_required
@superuser_required
@require_POST
def admin_product_image_primary_view(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    services.set_primary_image(image=image)
    return JsonResponse({"success": True, "primary_id": image.pk})


@login_required
@superuser_required
@require_POST
def admin_category_image_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    services.remove_category_image(category=category)
    return JsonResponse({"success": True})







