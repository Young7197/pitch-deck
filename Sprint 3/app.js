const PLAYER_ANIMATION_MS = 500;
const BOT_PLAY_DELAY_MS = 520;
const TRICK_CLEAR_DELAY_MS = 900;

const PLAYER_CLASS_NAMES = {
    "Player 1": "player1",
    "Player 2": "player2",
    "Player 3": "player3",
    "Player 4": "player4",
};

const BOT_COUNT_KEYS = {
    "Player 2": "player2",
    "Player 3": "player3",
    "Player 4": "player4",
};

const PLAYER_ROTATIONS = {
    "Player 1": "4deg",
    "Player 2": "-9deg",
    "Player 3": "2deg",
    "Player 4": "9deg",
};

document.addEventListener("DOMContentLoaded", () => {
    initializeBidControls();
    initializeAnimatedBoard();
});

function initializeBidControls() {
    const bidForm = document.getElementById("bid-form");
    const bidInput = document.getElementById("bid-input");
    const decreaseBidButton = document.getElementById("decrease-bid");
    const increaseBidButton = document.getElementById("increase-bid");

    if (!bidForm || !bidInput || !decreaseBidButton || !increaseBidButton) {
        return;
    }

    const minBid = 0;
    const maxBid = 18;
    const clampBid = (value) => Math.min(maxBid, Math.max(minBid, value));

    const updateBidValue = (nextValue) => {
        const safeValue = clampBid(nextValue);
        bidInput.value = safeValue.toString();
    };

    decreaseBidButton.addEventListener("click", () => {
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid - 1);
    });

    increaseBidButton.addEventListener("click", () => {
        const currentBid = Number.parseInt(bidInput.value, 10) || 0;
        updateBidValue(currentBid + 1);
    });

    bidForm.addEventListener("submit", (event) => {
        const selectedBid = Number.parseInt(bidInput.value, 10);

        if (Number.isNaN(selectedBid)) {
            event.preventDefault();
            updateBidValue(minBid);
            return;
        }

        updateBidValue(selectedBid);
    });
}

function initializeAnimatedBoard() {
    const board = document.getElementById("game-board");
    const stateElement = document.getElementById("initial-game-state");
    const playerHand = document.getElementById("player-hand");
    const tableCards = document.getElementById("table-cards");
    const feedback = document.getElementById("play-feedback");

    if (!board || !stateElement || !playerHand || !tableCards || !feedback) {
        return;
    }

    const botHands = {
        "Player 2": document.getElementById("bot-hand-player2"),
        "Player 3": document.getElementById("bot-hand-player3"),
        "Player 4": document.getElementById("bot-hand-player4"),
    };

    const trickSlots = {};
    document.querySelectorAll(".trick-slot").forEach((slot) => {
        trickSlots[slot.dataset.player] = slot;
    });

    let state;

    try {
        state = JSON.parse(stateElement.textContent);
    } catch (error) {
        console.error("Failed to parse initial game state.", error);
        return;
    }

    let isAnimating = false;
    let clearPromise = null;

    const cardBackImage = state.card_back_image || board.dataset.cardBack;
    let pendingOpeningPlays = Array.isArray(state.pending_auto_plays) ? [...state.pending_auto_plays] : [];
    let finalBotHandCounts = { ...state.bot_hand_counts };
    let finalCanPlayNow = Boolean(state.can_play_now);

    const applyPendingOpeningRollback = () => {
        // When bots must open a trick, the server already knows the resolved cards.
        // The client rewinds the visual state so those cards can still animate in.
        if (!state.opening_trick_pending || pendingOpeningPlays.length === 0) {
            return;
        }

        state.table_cards = [];
        state.bot_hand_counts = inflateBotHandCounts(finalBotHandCounts, pendingOpeningPlays);
        state.can_play_now = false;
    };

    applyPendingOpeningRollback();

    const canInteract = () => Boolean(state.can_play_now) && !isAnimating && !clearPromise;

    const syncCardButtons = () => {
        playerHand.querySelectorAll(".player-card-button").forEach((button) => {
            button.disabled = !canInteract();
        });
    };

    const hideFeedback = () => {
        feedback.hidden = true;
        feedback.textContent = "";
    };

    const showFeedback = (message) => {
        feedback.hidden = false;
        feedback.textContent = message;
    };

    const renderPlayerHand = () => {
        playerHand.replaceChildren();

        state.hand_images.forEach((imagePath, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "card-button player-card-button";
            button.dataset.index = index.toString();
            button.dataset.image = imagePath;
            button.disabled = !canInteract();

            const image = document.createElement("img");
            image.src = imagePath;
            image.className = "card-image";
            image.alt = "Player 1 card";

            button.appendChild(image);
            playerHand.appendChild(button);
        });
    };

    const renderSingleBotHand = (player, count) => {
        const container = botHands[player];

        if (!container) {
            return;
        }

        container.replaceChildren();

        for (let index = 0; index < count; index += 1) {
            const image = document.createElement("img");
            image.src = cardBackImage;
            image.className = "card-image";
            image.alt = `${player} card back`;
            container.appendChild(image);
        }
    };

    const renderBotHands = () => {
        Object.entries(BOT_COUNT_KEYS).forEach(([player, key]) => {
            renderSingleBotHand(player, state.bot_hand_counts[key] || 0);
        });
    };

    const renderTableCards = () => {
        tableCards.replaceChildren();

        state.table_cards.forEach((card, index) => {
            const image = document.createElement("img");
            image.src = card.card_image;
            image.alt = `${card.player} played card`;
            image.dataset.player = card.player;
            image.className = `table-card table-card--${PLAYER_CLASS_NAMES[card.player] || "player1"} card-image`;
            image.style.zIndex = (index + 1).toString();
            tableCards.appendChild(image);
        });
    };

    const renderBoard = () => {
        renderPlayerHand();
        renderBotHands();
        renderTableCards();
        syncCardButtons();
    };

    const getSourceElementRect = (sourceElement) => {
        const rect = sourceElement.getBoundingClientRect();

        if (rect.width > 0 && rect.height > 0) {
            return rect;
        }

        return null;
    };

    const animateToSlot = async ({ sourceElement, imagePath, player, hideSource = false }) => {
        const targetSlot = trickSlots[player];
        const sourceRect = getSourceElementRect(sourceElement);

        if (!targetSlot || !sourceRect) {
            return;
        }

        const targetRect = targetSlot.getBoundingClientRect();
        const flightCard = document.createElement("img");
        flightCard.src = imagePath;
        flightCard.className = "card-image card-flight";
        flightCard.alt = `${player} played card`;
        flightCard.style.left = `${sourceRect.left}px`;
        flightCard.style.top = `${sourceRect.top}px`;
        flightCard.style.width = `${sourceRect.width}px`;
        flightCard.style.height = `${sourceRect.height}px`;
        flightCard.style.setProperty("--flight-rotation", PLAYER_ROTATIONS[player] || "0deg");

        if (hideSource) {
            sourceElement.classList.add("is-source-hidden");
        }

        document.body.appendChild(flightCard);

        await waitForNextFrame();

        flightCard.classList.add("is-playing-to-center");
        flightCard.style.left = `${targetRect.left}px`;
        flightCard.style.top = `${targetRect.top}px`;
        flightCard.style.width = `${targetRect.width}px`;
        flightCard.style.height = `${targetRect.height}px`;

        await wait(PLAYER_ANIMATION_MS);
        flightCard.remove();
    };

    const requestPlay = async (index) => {
        const body = new URLSearchParams({ index: index.toString() });
        const response = await fetch("/play_card", {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
            body,
            credentials: "same-origin",
        });

        const payload = await response.json();

        if (!response.ok || payload.ok === false) {
            throw new Error(payload.error || "Unable to play the selected card.");
        }

        return payload;
    };

    const requestTrickClear = async () => {
        const response = await fetch("/clear_trick", {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
        });

        const payload = await response.json();

        if (!response.ok || payload.ok === false) {
            throw new Error(payload.error || "Unable to clear the completed trick.");
        }

        return payload;
    };

    const scheduleTrickClear = async () => {
        if (!state.trick_complete) {
            return;
        }

        if (clearPromise) {
            return clearPromise;
        }

        isAnimating = true;
        syncCardButtons();

        clearPromise = (async () => {
            await wait(TRICK_CLEAR_DELAY_MS);

            try {
                const payload = await requestTrickClear();
                state.table_cards = Array.isArray(payload.table_cards) ? payload.table_cards : [];
                state.trick_complete = Boolean(payload.trick_complete);
                state.can_play_now = Boolean(payload.can_play_now);
                state.opening_trick_pending = Boolean(payload.opening_trick_pending);
                pendingOpeningPlays = Array.isArray(payload.pending_auto_plays) ? [...payload.pending_auto_plays] : [];
                finalBotHandCounts = payload.bot_hand_counts ? { ...payload.bot_hand_counts } : { ...state.bot_hand_counts };
                finalCanPlayNow = Boolean(payload.can_play_now);
                state.bot_hand_counts = payload.bot_hand_counts ? { ...payload.bot_hand_counts } : state.bot_hand_counts;
            } catch (error) {
                console.error(error);
                state.table_cards = [];
                state.trick_complete = false;
                state.can_play_now = false;
                state.opening_trick_pending = false;
                pendingOpeningPlays = [];
            }

            applyPendingOpeningRollback();
            renderTableCards();

            if (state.opening_trick_pending && pendingOpeningPlays.length > 0) {
                clearPromise = null;
                await runPendingOpeningSequence();
                return;
            }

            clearPromise = null;
            isAnimating = false;
            syncCardButtons();
        })();

        return clearPromise;
    };

    const recoverFromPlayError = (message) => {
        showFeedback(message);
        window.setTimeout(() => {
            window.location.assign("/game");
        }, 900);
    };

    const handleCardPlay = async (button) => {
        hideFeedback();
        isAnimating = true;
        syncCardButtons();

        const selectedIndex = Number.parseInt(button.dataset.index, 10);
        const selectedImage = button.dataset.image;
        const playRequest = requestPlay(selectedIndex);

        button.classList.add("card-button--pending");

        try {
            await animateToSlot({
                sourceElement: button,
                imagePath: selectedImage,
                player: "Player 1",
                hideSource: true,
            });

            const payload = await playRequest;
            state.hand_images = Array.isArray(payload.hand_images) ? payload.hand_images : state.hand_images;
            state.table_cards = payload.player_card
                ? [...state.table_cards, payload.player_card]
                : state.table_cards;
            state.can_play_now = Boolean(payload.can_play_now);
            renderPlayerHand();
            renderTableCards();

            const nextBotCounts = { ...state.bot_hand_counts };

            for (const botPlay of payload.bot_plays || []) {
                await wait(BOT_PLAY_DELAY_MS);

                const sourceElement = botHands[botPlay.player]?.querySelector(".card-image:last-child") || botHands[botPlay.player];

                if (sourceElement) {
                    await animateToSlot({
                        sourceElement,
                        imagePath: cardBackImage,
                        player: botPlay.player,
                        hideSource: true,
                    });
                }

                state.table_cards = [...state.table_cards, {
                    player: botPlay.player,
                    card_image: botPlay.card_image,
                }];
                renderTableCards();

                const botKey = BOT_COUNT_KEYS[botPlay.player];
                if (botKey) {
                    nextBotCounts[botKey] = typeof botPlay.remaining_hand_count === "number"
                        ? botPlay.remaining_hand_count
                        : Math.max(0, (nextBotCounts[botKey] || 0) - 1);

                    state.bot_hand_counts = nextBotCounts;
                    renderSingleBotHand(botPlay.player, nextBotCounts[botKey]);
                }
            }

            state.bot_hand_counts = payload.bot_hand_counts || state.bot_hand_counts;
            state.table_cards = Array.isArray(payload.table_cards) ? payload.table_cards : state.table_cards;
            state.trick_complete = Boolean(payload.trick_complete);
            state.can_play_now = Boolean(payload.can_play_now);
            renderBotHands();
            renderTableCards();

            if (state.trick_complete) {
                await scheduleTrickClear();
                return;
            }
        } catch (error) {
            console.error(error);
            recoverFromPlayError(error.message || "Could not play the selected card.");
            return;
        } finally {
            if (!clearPromise) {
                isAnimating = false;
                syncCardButtons();
            }
        }
    };

    playerHand.addEventListener("click", (event) => {
        const button = event.target.closest(".player-card-button");

        if (!button || !canInteract()) {
            return;
        }

        handleCardPlay(button);
    });

    const runPendingOpeningSequence = async () => {
        if (!state.opening_trick_pending || pendingOpeningPlays.length === 0) {
            return;
        }

        hideFeedback();
        isAnimating = true;
        syncCardButtons();

        // Animate each previously resolved bot lead into the table before the user gains control.
        for (const [index, botPlay] of pendingOpeningPlays.entries()) {
            await wait(index === 0 ? 240 : BOT_PLAY_DELAY_MS);

            const sourceElement = botHands[botPlay.player]?.querySelector(".card-image:last-child") || botHands[botPlay.player];
            if (sourceElement) {
                await animateToSlot({
                    sourceElement,
                    imagePath: cardBackImage,
                    player: botPlay.player,
                    hideSource: true,
                });
            }

            state.table_cards = [...state.table_cards, {
                player: botPlay.player,
                card_image: botPlay.card_image,
            }];
            renderTableCards();

            const botKey = BOT_COUNT_KEYS[botPlay.player];
            if (botKey) {
                state.bot_hand_counts[botKey] = botPlay.remaining_hand_count;
                renderSingleBotHand(botPlay.player, botPlay.remaining_hand_count);
            }
        }

        state.bot_hand_counts = finalBotHandCounts;
        state.opening_trick_pending = false;
        state.pending_auto_plays = [];
        state.can_play_now = finalCanPlayNow;
        isAnimating = false;
        syncCardButtons();
    };

    renderBoard();

    if (state.opening_trick_pending && pendingOpeningPlays.length > 0) {
        runPendingOpeningSequence();
        return;
    }

    if (state.trick_complete && state.table_cards.length > 0) {
        scheduleTrickClear();
    }
}

function inflateBotHandCounts(finalCounts, pendingPlays) {
    const inflatedCounts = { ...finalCounts };

    // The server counts are post-play counts, so we add back pending opening plays
    // to recreate the pre-animation visual stack for each bot.
    pendingPlays.forEach((botPlay) => {
        const botKey = BOT_COUNT_KEYS[botPlay.player];
        if (!botKey) {
            return;
        }

        inflatedCounts[botKey] = (inflatedCounts[botKey] || 0) + 1;
    });

    return inflatedCounts;
}

function wait(durationMs) {
    return new Promise((resolve) => {
        window.setTimeout(resolve, durationMs);
    });
}

function waitForNextFrame() {
    return new Promise((resolve) => {
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(resolve);
        });
    });
}
