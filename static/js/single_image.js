document.addEventListener("DOMContentLoaded", () => {
    const MAX_BYTES = 5 * 1024 * 1024;
    const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

    async function postJson(url) {
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": CSRF_TOKEN },
                body: new FormData(),
            });
            let data = null;
            try { data = await response.json(); } catch (_) { /* non-JSON error page */ }
            return data || { success: false, error: `Request failed (${response.status}).` };
        } catch (_) {
            return { success: false, error: "Network error. Please try again." };
        }
    }

    function validate(file) {
        if (!ALLOWED_TYPES.includes(file.type)) return `${file.name} is not a JPG, PNG, WebP or GIF image.`;
        if (file.size > MAX_BYTES) return `${file.name} is larger than 5MB.`;
        return null;
    }

    document.querySelectorAll(".js-single-image").forEach((root) => {
        const input = root.querySelector(".js-single-input");
        const zone = root.querySelector(".js-single-zone");
        const title = root.querySelector(".js-single-title");
        const preview = root.querySelector(".single-image__preview");
        const img = preview.querySelector("img");
        const tag = root.querySelector(".js-single-tag");
        const removeBtn = root.querySelector(".js-single-remove");
        const removeUrl = root.dataset.removeUrl;

        let saved = Boolean(removeUrl);                 // the server already has an image
        let savedSrc = img.getAttribute("src") || "";
        let pending = false;                            // a new file is waiting for the form submit
        let objectUrl = null;

        function refresh() {
            if (pending) {
                img.src = objectUrl;
                preview.hidden = false;
                tag.textContent = "New image";
                title.textContent = "Choose a different image";
            } else if (saved) {
                img.src = savedSrc;
                preview.hidden = false;
                tag.textContent = "";
                title.textContent = "Replace image";
            } else {
                img.removeAttribute("src");
                preview.hidden = true;
                tag.textContent = "";
                title.textContent = "Click to choose an image";
            }
        }

        function clearPending() {
            if (objectUrl) URL.revokeObjectURL(objectUrl);
            objectUrl = null;
            pending = false;
            input.value = "";
            refresh();
        }

        function setFile(file) {
            const error = validate(file);
            if (error) {
                clearPending();          // never leave the UI out of sync with the input
                showToast(error, "error");
                return;
            }
            if (objectUrl) URL.revokeObjectURL(objectUrl);
            objectUrl = URL.createObjectURL(file);
            pending = true;
            refresh();
        }

        input.addEventListener("change", () => {
            if (input.files.length) setFile(input.files[0]);
        });

        zone.addEventListener("dragover", (event) => { event.preventDefault(); zone.classList.add("is-dragover"); });
        ["dragleave", "dragend"].forEach((name) =>
            zone.addEventListener(name, () => zone.classList.remove("is-dragover")));
        zone.addEventListener("drop", (event) => {
            event.preventDefault();
            zone.classList.remove("is-dragover");
            const file = event.dataTransfer.files[0];
            if (!file) return;
            const transfer = new DataTransfer();   // keep only the first file; this input takes one
            transfer.items.add(file);
            input.files = transfer.files;
            setFile(file);
        });

        removeBtn.addEventListener("click", async () => {
            if (pending) { clearPending(); return; }   // just drop the unsaved choice
            if (!saved) return;
            if (!window.confirm("Remove this image? It will be deleted permanently.")) return;

            preview.classList.add("is-busy");
            const result = await postJson(removeUrl);
            preview.classList.remove("is-busy");

            if (result.success) {
                saved = false;
                savedSrc = "";
                refresh();
                showToast("Image removed.");
            } else {
                showToast(result.error || "Could not remove the image.", "error");
            }
        });

        refresh();
    });
});





