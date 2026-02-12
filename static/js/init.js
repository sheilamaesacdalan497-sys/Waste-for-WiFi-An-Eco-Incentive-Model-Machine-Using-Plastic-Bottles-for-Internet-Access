import { $, openModal, closeModal, showToast } from './dom.js';
import { setSessionFromUrl } from './session.js';
import { formatTime, getUrlParam, getCurrentTimestamp } from './utils.js';
import { startBottleTimer, stopBottleTimer, registerBottle } from './timer.js';

let timerInterval = null;

// Update timer display and handle countdown
function updateTimer(sessionData) {
  const timerCard = $('timer-card');
  const timerEl = $('timer');
  
  if (!sessionData || !sessionData.expires_at) {
    if (timerCard) timerCard.style.display = 'none';
    return;
  }
  
  // Calculate remaining time
  const now = getCurrentTimestamp();
  const expiresAt = sessionData.expires_at;
  let remaining = expiresAt - now;
  
  if (remaining <= 0) {
    timerEl.textContent = 'Expired';
    timerCard.style.display = 'block';
    showToast('Your session has expired. Insert more bottles to continue.');
    if (timerInterval) clearInterval(timerInterval);
    return;
  }
  
  // Show timer card
  timerCard.style.display = 'block';
  timerEl.textContent = formatTime(remaining);
  
  // Start countdown
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      timerEl.textContent = 'Expired';
      clearInterval(timerInterval);
      showToast('Your session has expired.');
    } else {
      timerEl.textContent = formatTime(remaining);
    }
  }, 1000);
}

// Fetch and update session timer
async function fetchAndUpdateSession(sessionId) {
  try {
    const response = await fetch(`/api/session/${sessionId}`);
    if (response.ok) {
      const sessionData = await response.json();
      updateTimer(sessionData);
    }
  } catch (error) {
    console.error('Failed to fetch session:', error);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  setSessionFromUrl();
  
  // Get current session and update timer
  const sessionId = getUrlParam('session');
  if (sessionId) {
    await fetchAndUpdateSession(sessionId);
  }

  // Button: Insert Bottle - start timer when modal opens
  const insertBtn = $('btn-insert-bottle');
  if (insertBtn) {
    insertBtn.addEventListener('click', () => {
      openModal('modal-insert-bottle');
      startBottleTimer(); // Start the 3-minute countdown
    });
  }

  // Button: How It Works
  const howBtn = $('btn-howitworks');
  if (howBtn) {
    howBtn.addEventListener('click', () => {
      openModal('modal-howitworks');
    });
  }

  // Button: Rate EcoNeT
  const rateBtn = $('btn-rate');
  if (rateBtn) {
    rateBtn.addEventListener('click', () => {
      window.location.href = '/rate.html';
    });
  }

  // Close modal buttons - stop timer when closing insert bottle modal
  const closeButtons = document.querySelectorAll('.modal-close');
  closeButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal');
      if (modal) {
        if (modal.id === 'modal-insert-bottle') {
          stopBottleTimer();
        }
        closeModal(modal.id);
      }
    });
  });

  // TODO: Add event listener for actual bottle insertion
  // This would come from your hardware/sensor integration
  // Example:
  // document.addEventListener('bottleInserted', () => {
  //   registerBottle();
  // });
});

// Export for use in other modules
export { updateTimer, fetchAndUpdateSession };
