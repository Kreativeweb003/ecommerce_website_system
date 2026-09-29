function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
}

const CSRF_TOKEN = getCookie("csrftoken");

/**
 * Shared fetch wrapper for every AJAX call in the store.
 * Always sends X-Requested-With so Django's is_ajax() check works,
 * and always sends the CSRF token since every endpoint here is POST-only.
 */
async function ajaxPost(url, formData) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": CSRF_TOKEN,
        },
        body: formData,
    });
    return response.json();
}

async function ajaxGet(url) {
    const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    return response.json();
}

function updateCartBadge(count) {
    const badge = document.querySelector(".js-cart-count");
    if (badge) badge.textContent = count;
}

function updateCartTotals(data) {
    if (data.total_items !== undefined) updateCartBadge(data.total_items);
    const subtotalEl = document.querySelector(".js-cart-subtotal");
    const discountEl = document.querySelector(".js-cart-discount");
    const totalEl = document.querySelector(".js-cart-total");
    if (subtotalEl && data.subtotal !== undefined) subtotalEl.textContent = `$${data.subtotal}`;
    if (discountEl && data.discount_amount !== undefined) discountEl.textContent = `-$${data.discount_amount}`;
    if (totalEl && data.total !== undefined) totalEl.textContent = `$${data.total}`;
}

function showToast(message, type = "success") {
    const container = document.querySelector(".js-toast-container") || (() => {
        const el = document.createElement("div");
        el.className = "js-toast-container";
        el.style.cssText = "position:fixed; bottom:20px; right:20px; z-index:100; display:flex; flex-direction:column; gap:8px;";
        document.body.appendChild(el);
        return el;
    })();

    const toast = document.createElement("div");
    toast.className = `alert alert--${type === "error" ? "error" : "success"}`;
    toast.style.cssText = "box-shadow:0 4px 16px rgba(0,0,0,0.12); min-width:240px;";
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3500);
}
