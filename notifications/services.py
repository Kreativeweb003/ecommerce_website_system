from .tasks import send_email_task, send_sms_task


def _get_preference(*, user):
    if not user:
        return None
    from .models import NotificationPreference
    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    return preference


def notify_order_confirmed(*, order):
    context = {
        "order_number": order.order_number,
        "customer_name": order.shipping_full_name,
        "items": [
            {"name": item.product_name, "quantity": item.quantity, "line_total": str(item.line_total)}
            for item in order.items.all()
        ],
        "subtotal": str(order.subtotal),
        "shipping_cost": str(order.shipping_cost),
        "discount_amount": str(order.discount_amount),
        "total": str(order.total),
    }
    send_email_task.delay(
        event_type="order_confirmed",
        recipient=order.email,
        subject=f"Order Confirmed - {order.order_number}",
        template_name="order_confirmed",
        context=context,
        user_id=order.user_id,
        reference=order.order_number,
    )


def notify_payment_failed(*, order, reason=""):
    context = {"order_number": order.order_number, "customer_name": order.shipping_full_name, "reason": reason}
    send_email_task.delay(
        event_type="payment_failed",
        recipient=order.email,
        subject=f"Payment Issue - Order {order.order_number}",
        template_name="payment_failed",
        context=context,
        user_id=order.user_id,
        reference=order.order_number,
    )


def notify_order_shipped(*, order, tracking_number=""):
    preference = _get_preference(user=order.user)

    context = {
        "order_number": order.order_number,
        "customer_name": order.shipping_full_name,
        "tracking_number": tracking_number,
    }

    if preference is None or preference.order_updates_email:
        send_email_task.delay(
            event_type="order_shipped",
            recipient=order.email,
            subject=f"Your order {order.order_number} has shipped",
            template_name="order_shipped",
            context=context,
            user_id=order.user_id,
            reference=order.order_number,
        )

    if preference and preference.order_updates_sms and order.phone_number:
        send_sms_task.delay(
            event_type="order_shipped",
            recipient=order.phone_number,
            message=f"Your order {order.order_number} has shipped.",
            user_id=order.user_id,
            reference=order.order_number,
        )


def notify_order_delivered(*, order):
    context = {"order_number": order.order_number, "customer_name": order.shipping_full_name}
    send_email_task.delay(
        event_type="order_delivered",
        recipient=order.email,
        subject=f"Your order {order.order_number} was delivered",
        template_name="order_delivered",
        context=context,
        user_id=order.user_id,
        reference=order.order_number,
    )


def notify_order_cancelled(*, order, reason=""):
    context = {"order_number": order.order_number, "customer_name": order.shipping_full_name, "reason": reason}
    send_email_task.delay(
        event_type="order_cancelled",
        recipient=order.email,
        subject=f"Order Cancelled - {order.order_number}",
        template_name="order_cancelled",
        context=context,
        user_id=order.user_id,
        reference=order.order_number,
    )


def notify_order_refunded(*, order, amount):
    context = {"order_number": order.order_number, "customer_name": order.shipping_full_name, "amount": str(amount)}
    send_email_task.delay(
        event_type="order_refunded",
        recipient=order.email,
        subject=f"Refund Processed - {order.order_number}",
        template_name="order_refunded",
        context=context,
        user_id=order.user_id,
        reference=order.order_number,
    )


def notify_low_stock(*, stock_item):
    from django.conf import settings
    item_label = str(stock_item.variant) if stock_item.variant else str(stock_item.product)

    context = {
        "item_label": item_label,
        "warehouse": stock_item.warehouse.name,
        "available_quantity": stock_item.available_quantity,
        "threshold": stock_item.low_stock_threshold,
    }
    send_email_task.delay(
        event_type="low_stock_alert",
        recipient=settings.INVENTORY_ALERT_EMAIL,
        subject=f"Low Stock Alert: {item_label}",
        template_name="low_stock_alert",
        context=context,
        user_id=None,
        reference=item_label,
    )


def notify_welcome(*, user):
    context = {"first_name": user.first_name}
    send_email_task.delay(
        event_type="welcome",
        recipient=user.email,
        subject="Welcome!",
        template_name="welcome",
        context=context,
        user_id=user.id,
        reference="",
    )


def notify_password_changed(*, user):
    context = {"first_name": user.first_name}
    send_email_task.delay(
        event_type="password_changed",
        recipient=user.email,
        subject="Your password was changed",
        template_name="password_changed",
        context=context,
        user_id=user.id,
        reference="",
    )




def notify_wishlist_price_drop(*, user, wishlist_item):
    item = wishlist_item.variant if wishlist_item.variant else wishlist_item.product
    context = {
        "first_name": user.first_name,
        "item_name": str(item),
        "old_price": str(wishlist_item.price_at_addition),
        "new_price": str(wishlist_item.current_price),
    }
    send_email_task.delay(
        event_type="wishlist_price_drop",
        recipient=user.email,
        subject=f"Price drop: {item}",
        template_name="wishlist_price_drop",
        context=context,
        user_id=user.id,
        reference=str(wishlist_item.pk),
    )


def notify_wishlist_back_in_stock(*, user, wishlist_item):
    item = wishlist_item.variant if wishlist_item.variant else wishlist_item.product
    context = {"first_name": user.first_name, "item_name": str(item)}
    send_email_task.delay(
        event_type="wishlist_back_in_stock",
        recipient=user.email,
        subject=f"Back in stock: {item}",
        template_name="wishlist_back_in_stock",
        context=context,
        user_id=user.id,
        reference=str(wishlist_item.pk),
    )
