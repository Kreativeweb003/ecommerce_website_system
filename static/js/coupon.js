document.addEventListener("DOMContentLoaded", () => {

    const applyForm = document.querySelector(".js-apply-coupon-form");
    if (applyForm) {
        applyForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const formData = new FormData(applyForm);
            const result = await ajaxPost("/coupons/apply/", formData);

            if (result.success) {
                updateCartTotals(result);
                showToast(`Coupon '${result.coupon_code}' applied.`);
            } else {
                showToast(result.error, "error");
            }
        });
    }

    const removeButton = document.querySelector(".js-remove-coupon");
    if (removeButton) {
        removeButton.addEventListener("click", async (event) => {
            event.preventDefault();
            const result = await ajaxPost("/coupons/remove/", new FormData());
            if (result.success) {
                updateCartTotals(result);
            }
        });
    }

});
