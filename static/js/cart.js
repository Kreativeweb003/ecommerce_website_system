document.addEventListener("DOMContentLoaded", () => {

    // Add to cart — <button class="js-add-to-cart" data-product-id="1" data-variant-id="">
    document.querySelectorAll(".js-add-to-cart").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const formData = new FormData();
            formData.append("product_id", button.dataset.productId);
            if (button.dataset.variantId) formData.append("variant_id", button.dataset.variantId);
            formData.append("quantity", button.dataset.quantity || 1);

            const result = await ajaxPost("/cart/add/", formData);
            if (result.success) {
                updateCartTotals(result);
                showToast("Item added to cart.");
            } else {
                showToast(result.error, "error");
            }
        });
    });

    // Add-to-cart form on the product detail page (supports variant select + quantity stepper)
    const addToCartForm = document.querySelector(".js-add-to-cart-form");
    if (addToCartForm) {
        addToCartForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const formData = new FormData(addToCartForm);
            const result = await ajaxPost(addToCartForm.action, formData);
            if (result.success) {
                updateCartTotals(result);
                showToast("Item added to cart.");
            } else {
                showToast(result.error, "error");
            }
        });
    }

    // Quantity update — <input class="js-cart-quantity" data-item-id="5">
    document.querySelectorAll(".js-cart-quantity").forEach((input) => {
        input.addEventListener("change", async () => {
            const formData = new FormData();
            formData.append("quantity", input.value);

            const result = await ajaxPost(`/cart/item/${input.dataset.itemId}/update/`, formData);
            if (result.success) {
                const lineTotalEl = document.querySelector(`.js-line-total-${result.item_id}`);
                if (lineTotalEl) lineTotalEl.textContent = `$${result.line_total}`;
                updateCartTotals(result);
            } else {
                showToast(result.error, "error");
            }
        });
    });

    // Remove item — <button class="js-cart-remove" data-item-id="5">
    document.querySelectorAll(".js-cart-remove").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const result = await ajaxPost(`/cart/item/${button.dataset.itemId}/remove/`, new FormData());
            if (result.success) {
                document.querySelector(`.js-cart-row-${result.item_id}`)?.remove();
                updateCartTotals(result);
            }
        });
    });

});
