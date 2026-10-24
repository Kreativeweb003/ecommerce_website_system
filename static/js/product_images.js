document.addEventListener("DOMContentLoaded", () => {
    const manager = document.getElementById("image-manager");
    if (!manager) return;

    const mode = manager.dataset.mode;            // "create" or "edit"
    const uploadUrl = manager.dataset.uploadUrl;  // edit mode only
    const input = document.getElementById("image-input");
    const zone = document.getElementById("image-zone");
    const grid = document.getElementById("image-grid");
    const counter = document.getElementById("image-count");
    const cardTemplate = document.getElementById("image-card-template");

    const MAX_BYTES = 5 * 1024 * 1024;
    const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

    let staged = []; // create mode: [{ file, objectUrl, card }]

    // ---------- helpers ----------

    async function postJson(url, formData) {
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": CSRF_TOKEN },
                body: formData || new FormData(),
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

    function makeCard({ src, id = "", deleteUrl = "", primaryUrl = "", primary = false, busy = false }) {
        const card = cardTemplate.content.firstElementChild.cloneNode(true);
        card.querySelector("img").src = src;
        card.dataset.id = id;
        card.dataset.deleteUrl = deleteUrl;
        card.dataset.primaryUrl = primaryUrl;
        card.classList.toggle("is-primary", primary);
        card.classList.toggle("is-busy", busy);
        return card;
    }

    function markPrimary(card) {
        if (!card) return;
        grid.querySelectorAll(".image-card.is-primary").forEach((c) => c.classList.remove("is-primary"));
        card.classList.add("is-primary");
        grid.prepend(card);
    }

    function updateUi() {
        const count = grid.querySelectorAll(".image-card").length;
        grid.hidden = count === 0;
        counter.textContent = count ? ` (${count} image${count === 1 ? "" : "s"})` : "";

        if (mode === "create") {
            grid.querySelectorAll(".image-card.is-primary").forEach((c) => c.classList.remove("is-primary"));
            const first = grid.querySelector(".image-card");
            if (first) first.classList.add("is-primary");
        }
    }

    // ---------- create mode: stage files, submit with the form ----------

    function syncInput() {
        const transfer = new DataTransfer();
        staged.forEach((entry) => transfer.items.add(entry.file));
        input.files = transfer.files;
    }

    function stageFiles(files) {
        for (const file of files) {
            const error = validate(file);
            if (error) { showToast(error, "error"); continue; }

            const duplicate = staged.some((s) =>
                s.file.name === file.name && s.file.size === file.size && s.file.lastModified === file.lastModified);
            if (duplicate) continue;

            const objectUrl = URL.createObjectURL(file);
            const card = makeCard({ src: objectUrl });
            grid.append(card);
            staged.push({ file, objectUrl, card });
        }
        syncInput();
        updateUi();
    }

    function removeStaged(card) {
        const index = staged.findIndex((s) => s.card === card);
        if (index === -1) return;
        URL.revokeObjectURL(staged[index].objectUrl);
        staged.splice(index, 1);
        card.remove();
        syncInput();
        updateUi();
    }

    function moveStagedToFront(card) {
        const index = staged.findIndex((s) => s.card === card);
        if (index <= 0) return;
        const [entry] = staged.splice(index, 1);
        staged.unshift(entry);
        grid.prepend(card);
        syncInput();
        updateUi();
    }

    // ---------- edit mode: upload immediately ----------

    function fillCard(card, data) {
        card.querySelector("img").src = data.thumb_url;
        card.dataset.id = data.id;
        card.dataset.deleteUrl = data.delete_url;
        card.dataset.primaryUrl = data.primary_url;
        card.classList.remove("is-busy");
        if (data.is_primary) markPrimary(card);
    }

    async function uploadFiles(files) {
        const jobs = [];
        for (const file of files) {
            const error = validate(file);
            if (error) { showToast(error, "error"); continue; }
            const objectUrl = URL.createObjectURL(file);
            const card = makeCard({ src: objectUrl, busy: true });
            grid.append(card);
            jobs.push({ file, card, objectUrl });
        }
        updateUi();

        for (const job of jobs) {
            const formData = new FormData();
            formData.append("images", job.file);
            const result = await postJson(uploadUrl, formData);
            URL.revokeObjectURL(job.objectUrl);

            if (result.success && result.images && result.images.length) {
                fillCard(job.card, result.images[0]);
            } else {
                job.card.remove();
                showToast((result.errors && result.errors[0]) || result.error || "Upload failed.", "error");
            }
            updateUi();
        }
    }

    // ---------- events ----------

    function handleFiles(fileList) {
        const files = Array.from(fileList); // copy first: syncInput() replaces input.files
        if (!files.length) return;
        if (mode === "create") stageFiles(files); else uploadFiles(files);
    }

    input.addEventListener("change", () => {
        handleFiles(input.files);
        if (mode === "edit") input.value = "";
    });

    zone.addEventListener("dragover", (event) => { event.preventDefault(); zone.classList.add("is-dragover"); });
    ["dragleave", "dragend"].forEach((name) =>
        zone.addEventListener(name, () => zone.classList.remove("is-dragover")));
    zone.addEventListener("drop", (event) => {
        event.preventDefault();
        zone.classList.remove("is-dragover");
        handleFiles(event.dataTransfer.files);
    });

    grid.addEventListener("click", async (event) => {
        const removeBtn = event.target.closest(".js-image-remove");
        const primaryBtn = event.target.closest(".js-image-primary");
        if (!removeBtn && !primaryBtn) return;

        const card = event.target.closest(".image-card");
        if (!card || card.classList.contains("is-busy")) return;

        if (mode === "create") {
            if (removeBtn) removeStaged(card); else moveStagedToFront(card);
            return;
        }

        if (removeBtn) {
            if (!window.confirm("Remove this image? It will be deleted permanently.")) return;
            card.classList.add("is-busy");
            const result = await postJson(card.dataset.deleteUrl);
            if (result.success) {
                card.remove();
                if (result.primary_id) {
                    markPrimary(grid.querySelector(`.image-card[data-id="${result.primary_id}"]`));
                }
                updateUi();
                showToast("Image removed.");
            } else {
                card.classList.remove("is-busy");
                showToast(result.error || "Could not remove the image.", "error");
            }
        } else {
            card.classList.add("is-busy");
            const result = await postJson(card.dataset.primaryUrl);
            card.classList.remove("is-busy");
            if (result.success) {
                markPrimary(card);
                showToast("Main image updated.");
            } else {
                showToast(result.error || "Could not update the main image.", "error");
            }
        }
    });

    updateUi();
});


