document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".js-wishlist-add").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const formData = new FormData();
            formData.append("product_id", button.dataset.productId);
            if (button.dataset.variantId) formData.append("variant_id", button.dataset.variantId);

            const result = await ajaxPost("/wishlist/add/", formData);
            showToast(result.success ? "Added to wishlist." : result.error, result.success ? "success" : "error");
        });
    });

    document.querySelectorAll(".js-wishlist-remove").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const result = await ajaxPost(`/wishlist/${button.dataset.itemId}/remove/`, new FormData());
            if (result.success) {
                document.querySelector(`.js-wishlist-row-${result.item_id}`)?.remove();
            }
        });
    });

    document.querySelectorAll(".js-wishlist-move-to-cart").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const result = await ajaxPost(`/wishlist/${button.dataset.itemId}/move-to-cart/`, new FormData());
            if (result.success) {
                document.querySelector(`.js-wishlist-row-${result.item_id}`)?.remove();
                updateCartBadge(result.total_items);
                showToast("Moved to cart.");
            } else {
                showToast(result.error, "error");
            }
        });
    });

});
