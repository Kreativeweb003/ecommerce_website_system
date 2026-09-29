document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".js-review-vote").forEach((button) => {
        button.addEventListener("click", async (event) => {
            event.preventDefault();
            const formData = new FormData();
            formData.append("vote", button.dataset.vote);

            const result = await ajaxPost(`/reviews/${button.dataset.reviewId}/vote/`, formData);
            if (result.success) {
                const row = button.closest(".review");
                if (row) {
                    const helpfulBtn = row.querySelector('[data-vote="helpful"]');
                    const notHelpfulBtn = row.querySelector('[data-vote="not_helpful"]');
                    if (helpfulBtn) helpfulBtn.textContent = `Helpful (${result.helpful_count})`;
                    if (notHelpfulBtn) notHelpfulBtn.textContent = `Not helpful (${result.not_helpful_count})`;
                }
            } else {
                showToast(result.error, "error");
            }
        });
    });

});
