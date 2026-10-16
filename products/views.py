from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from reviews.services import get_approved_reviews_for_product, get_product_rating_summary, get_existing_review
from core.permissions import superuser_required
from django.core.exceptions import ValidationError

from . import services
from .forms import ProductForm, ProductImageForm, ProductFilterForm, ProductVariantForm, CategoryForm
from .models import Product, Category 


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
            product = services.create_product(data=form.cleaned_data, images=images)
            messages.success(request, "Product created successfully.")
            return redirect("products:product_detail", slug=product.slug)
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
            return redirect("products:product_detail", slug=product.slug)
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

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("products:admin_category_list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "products/admin_category_form.html", {
        "form": form, "action": "Edit", "category": category,
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

