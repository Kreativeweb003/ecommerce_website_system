from django import template

from reviews.services import get_product_rating_summary

register = template.Library()


@register.simple_tag
def product_rating(product):
    """
    Returns the same rating summary used on the product detail page,
    so product cards can show stars and a review count.
    Usage: {% product_rating product as rating %}
    """
    return get_product_rating_summary(product=product)