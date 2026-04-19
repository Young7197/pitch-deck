
document.addEventListener("DOMContentLoaded", () => {
    // The bid modal exists only when the player has not selected a bid yet.
    const bidForm = document.getElementById("bid-form");
    const bidInput = document.getElementById("bid-input");
    const decreaseBidButton = document.getElementById("decrease-bid");
    const increaseBidButton = document.getElementById("increase-bid");

    if (!bidForm || !bidInput || !decreaseBidButton || !increaseBidButton) {
        return;
    }

    //Set min a max values for the bid for higher robustness
    const minBid = 0;
    const maxBid = 18;

    // Keep every update inside the valid range to avoid invalid form submissions.
    const clampBid = (value) => Math.min(maxBid, Math.max(minBid, value));

    //Update bid value logic
    const updateBidValue = (nextValue) => {
        const safeValue = clampBid(nextValue);
        bidInput.value = safeValue.toString();
    };

    //Decrease bid button logic
    decreaseBidButton.addEventListener("click", () => {
        //Parse as a decimal number
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid - 1);
    });

    //Increase bid button logic
    increaseBidButton.addEventListener("click", () => {
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid + 1);
    });

    //Bid form submit logic
    bidForm.addEventListener("submit", (event) => {
        const selectedBid = Number.parseInt(bidInput.value, 10);

        // If the value is malformed, prevent submit and reset to a safe default.
        if (Number.isNaN(selectedBid)) {
            event.preventDefault();
            updateBidValue(minBid);
            return;
        }
        //If bid is valid, update bid value
        updateBidValue(selectedBid);
    });
});
