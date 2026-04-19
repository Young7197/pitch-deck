document.addEventListener("DOMContentLoaded", () => {
    // The bid modal exists only when the player has not selected a bid yet.
    const bidForm = document.getElementById("bid-form");
    const bidInput = document.getElementById("bid-input");
    const decreaseBidButton = document.getElementById("decrease-bid");
    const increaseBidButton = document.getElementById("increase-bid");

    if (!bidForm || !bidInput || !decreaseBidButton || !increaseBidButton) {
        return;
    }

    // Keep the bid within the game rules.
    const minBid = 0;
    const maxBid = 18;

    // Keep every update inside the valid range to avoid invalid form submissions.
    const clampBid = (value) => Math.min(maxBid, Math.max(minBid, value));

    // Sync the numeric input with a validated bid value.
    const updateBidValue = (nextValue) => {
        const safeValue = clampBid(nextValue);
        bidInput.value = safeValue.toString();
    };

    // Move the selected bid down by one step.
    decreaseBidButton.addEventListener("click", () => {
        // Parse the input as a base-10 number before updating it.
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid - 1);
    });

    // Move the selected bid up by one step.
    increaseBidButton.addEventListener("click", () => {
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid + 1);
    });

    // Validate once more before the value is submitted to the backend.
    bidForm.addEventListener("submit", (event) => {
        const selectedBid = Number.parseInt(bidInput.value, 10);

        // If the value is malformed, prevent submit and reset to a safe default.
        if (Number.isNaN(selectedBid)) {
            event.preventDefault();
            updateBidValue(minBid);
            return;
        }

        // Clamp the final value so the submitted payload always respects the allowed range.
        updateBidValue(selectedBid);
    });
});