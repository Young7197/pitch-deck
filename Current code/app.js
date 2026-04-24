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
    const canInteract = () => Boolean(state.can_play) && !isAnimating && !clearPromise;

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
            } catch (error) {
                console.error(error);
                state.table_cards = [];
                state.trick_complete = false;
            }

            renderTableCards();
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
            state.table_cards = payload.player_card ? [payload.player_card] : [];
            renderPlayerHand();
            renderTableCards();

            const nextBotCounts = { ...state.bot_hand_counts };

            for (const botPlay of payload.bot_plays || []) {
                await wait(BOT_PLAY_DELAY_MS);

                const sourceElement = botHands[botPlay.player];

                try {
                    if (sourceElement) {
                        await animateToSlot({
                            sourceElement,
                            imagePath: cardBackImage,
                            player: botPlay.player,
                            hideSource: true,
                        });
                    }
                } catch (error) {
                    console.error("Animation failed:", error);
                    // DO NOT stop execution — continue game
                }

                // Always update table even if animation fails
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
            renderBotHands();
            renderTableCards();

            if (state.trick_complete) {
                await scheduleTrickClear();

                // NEW: check if round is over
                if (payload.round_over) {
                    showRoundEndModal();
                    return;
                }

                return;
            }
        } catch (error) {
            console.error(error);
            recoverFromPlayError(error.message || "Could not play the selected card.");
            return;
        } finally {
            isAnimating = false;
            syncCardButtons();
        }
    };

    playerHand.addEventListener("click", (event) => {
        const button = event.target.closest(".player-card-button");

        if (!button || !canInteract()) {
            return;
        }

        handleCardPlay(button);
    });

    renderBoard();

    if (state.trick_complete && state.table_cards.length > 0) {
        scheduleTrickClear();
    }
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

async function playCard(index, element) {
    // 1. Prepare the data to send to Python
    const formData = new FormData();
    formData.append('index', index);

    try {
        // 2. Call the play_card route
        const response = await fetch('/play_card', {
            method: 'POST',
            body: formData,
            // THIS HEADER IS KEY: It triggers your is_json_request() helper in app.py
            headers: { 
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (data.ok) {
            // Remove the card from the user's visual hand
            element.parentElement.removeChild(element);

            // Place the user's card on the table
            renderToTable(data.player_card_image, 'slot-p1');

            // Animate bot plays with a staggered delay
            data.bot_plays.forEach((play, i) => {
                setTimeout(() => {
                    renderToTable(play.card_image, `slot-p${i + 2}`);
                }, (i + 1) * 600);
            });

            // If the trick is done, clear the board after 2 seconds
            if (data.trick_complete) {
                setTimeout(() => {
                    document.querySelectorAll('.slot').forEach(slot => slot.innerHTML = '');
                }, 2500);
            }
        } else {
            console.error("Game Error:", data.error);
            alert(data.error); // Tells you if you need to bid/set trump first
        }
    } catch (error) {
        console.error("Network Error:", error);
    }
}

function renderToTable(imgSrc, slotId) {
    const slot = document.getElementById(slotId);
    if(slot) {
        slot.innerHTML = `<img src="${imgSrc}" class="card-img animate-in">`;
    }
}

// Global state for selected discards
let selectedDiscardIndices = [];

// 1. Function to show the modal and fetch data
async function checkAndInitiateDiscardPhase() {
    console.log("Checking for Discard Phase...");
    const response = await fetch('/get_discard_status', {
        headers: { 'Accept': 'application/json' }
    });
    const data = await response.json();

    if (data.ok && data.show_discard) {
        // Prepare Modal UI
        selectedDiscardIndices = []; // reset
        const modal = document.getElementById('discard-modal');
        const trumpSpan = document.getElementById('discard-trump-name');
        const handDisplay = document.getElementById('discard-hand-display');

        trumpSpan.innerText = data.trump_suit;
        handDisplay.innerHTML = ''; // clear existing

        // Render hand for discarding
        data.hand.forEach(cardData => {
            const wrapper = document.createElement('div');
            wrapper.className = 'discard-card-wrapper';
            wrapper.id = `wrapper-${cardData.index}`;
            
            const img = document.createElement('img');
            img.src = cardData.image;
            img.className = 'card-img'; // Use existing styling
            img.alt = cardData.display_name;
            wrapper.appendChild(img);

            if (cardData.can_discard) {
                wrapper.onclick = () => toggleDiscardSelection(cardData.index);
            } else {
                // Rule: Cannot discard Trump
                wrapper.className += ' disabled';
            }
            handDisplay.appendChild(wrapper);
        });

        // Show Modal
        modal.style.display = 'flex';
    } else {
        // If phase already completed or not time yet, allow play.
        console.log("Discard Phase skipped or not initialized.");
    }
}

// 2. Handle selection UI
function toggleDiscardSelection(index) {
    const wrapper = document.getElementById(`wrapper-${index}`);
    
    if (wrapper.classList.contains('selected')) {
        wrapper.classList.remove('selected');
        // remove index
        selectedDiscardIndices = selectedDiscardIndices.filter(i => i !== index);
    } else {
        wrapper.classList.add('selected');
        selectedDiscardIndices.push(index);
    }
    
    // Update button text to be helpful
    const btn = document.getElementById('discard-submit-btn');
    if(selectedDiscardIndices.length > 0) {
        btn.innerText = `Complete Discard (${selectedDiscardIndices.length} cards)`;
    } else {
        btn.innerText = `Complete Discard`;
    }
}

// 3. Submit selected indices to Python
async function submitDiscards() {
    // We send empty indices if they simply click the submit button with no selection.
    
    const response = await fetch('/process_discards', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ indices: selectedDiscardIndices })
    });

    const data = await response.json();

    if (data.ok) {
        const playerHand = document.getElementById('player-hand');
        playerHand.innerHTML = '';

        data.new_hand_images.forEach((img_path, idx) => {
            const button = document.createElement('button');
            button.type = "button";
            button.className = "card-button player-card-button";
            button.dataset.index = idx;
            button.dataset.image = img_path;

            const img = document.createElement('img');
            img.src = img_path;
            img.className = 'card-image';

            button.appendChild(img);

            // IMPORTANT: hook back into your main click system
            button.addEventListener("click", (event) => {
                const btn = event.currentTarget;
                const board = document.getElementById("game-board");
                if (!board) return;

                // simulate normal click flow
                btn.dispatchEvent(new Event("click", { bubbles: true }));
            });

            playerHand.appendChild(button);
        });

        closeDiscardModal();
    } else {
        alert("Error during discard: " + data.error);
    }
}

// Standard exit functions
function closeDiscardModal() {
    document.getElementById('discard-modal').style.display = 'none';
}

// AUTOMATION: Hook into the trump selection logic
function onTrumpSubmit() {
}

document.addEventListener("DOMContentLoaded", () => {
    // 1. Grab the state from the script tag you already have in game.html
    const gameState = JSON.parse(document.getElementById("initial-game-state").textContent);

    // 2. If the Python flag says we need to discard, fire the function!
    if (gameState.needs_discard) {
        console.log("Discard phase triggered!");
        checkAndInitiateDiscardPhase(); // This calls the function you wrote in Step 2
    }
});

function openDiscardModal() {
    fetch('/get_discard_data')
        .then(res => res.json())
        .then(data => {
            if(data.ok) {
                // Code to populate 'discard-hand-display' in game.html
                document.getElementById('discard-modal').style.display = 'flex';
            }
        });
}

// Ensure you are appending the cards to 'discard-hand-display'
function updateDiscardUI(handData) {
    const display = document.getElementById('discard-hand-display');
    display.innerHTML = ''; // Clear existing
    
    handData.forEach(card => {
        const wrapper = document.createElement('div');
        wrapper.className = 'discard-card-wrapper' + (card.can_discard ? '' : ' disabled');
        
        const img = document.createElement('img');
        img.src = card.image;
        img.className = 'card-image'; // This will now be shrunk by the CSS above
        
        wrapper.appendChild(img);
        display.appendChild(wrapper);
    });
}

function showRoundEndModal() {
    const modal = document.getElementById("round-end-modal");
    if (modal) {
        modal.style.display = "flex";
    }
}