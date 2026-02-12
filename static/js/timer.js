import { $, closeModal, showToast } from './dom.js';
import { formatTime } from './utils.js';

const BOTTLE_TIMER_DURATION = 5; // 3 minutes in seconds
let bottleTimerInterval = null;
let bottleTimeRemaining = BOTTLE_TIMER_DURATION;
let bottleCount = 0;

// Start the bottle insertion timer
export function startBottleTimer() {
  bottleTimeRemaining = BOTTLE_TIMER_DURATION;
  bottleCount = 0;
  
  const progressBar = $('bottle-progress');
  const countdownEl = $('bottle-countdown');
  const bottleCountEl = $('bottle-count');
  const timeEarnedEl = $('time-earned');
  
  // Reset UI
  if (progressBar) progressBar.style.width = '100%';
  if (countdownEl) countdownEl.textContent = formatTime(bottleTimeRemaining);
  if (bottleCountEl) bottleCountEl.textContent = '0';
  if (timeEarnedEl) timeEarnedEl.textContent = '0 minutes';
  
  // Clear existing interval
  if (bottleTimerInterval) clearInterval(bottleTimerInterval);
  
  // Start countdown
  bottleTimerInterval = setInterval(() => {
    bottleTimeRemaining--;
    
    // Update countdown text
    if (countdownEl) {
      countdownEl.textContent = formatTime(bottleTimeRemaining);
    }
    
    // Update progress bar
    if (progressBar) {
      const percentage = (bottleTimeRemaining / BOTTLE_TIMER_DURATION) * 100;
      progressBar.style.width = `${percentage}%`;
    }
    
    // Timer finished
    if (bottleTimeRemaining <= 0) {
      clearInterval(bottleTimerInterval);
      bottleTimerInterval = null;
      
      if (bottleCount > 0) {
        showToast(`Session started! You earned ${bottleCount * 2} minutes of Wi-Fi.`);
        closeModal('modal-insert-bottle');
        // TODO: Start Wi-Fi session with earned time
      } else {
        showToast('Time expired. No bottles inserted.');
        closeModal('modal-insert-bottle');
      }
    }
  }, 1000);
}

// Stop the timer
export function stopBottleTimer() {
  if (bottleTimerInterval) {
    clearInterval(bottleTimerInterval);
    bottleTimerInterval = null;
  }
}

// Register a bottle insertion
export function registerBottle() {
  bottleCount++;
  
  const bottleCountEl = $('bottle-count');
  const timeEarnedEl = $('time-earned');
  
  if (bottleCountEl) {
    bottleCountEl.textContent = bottleCount.toString();
  }
  
  if (timeEarnedEl) {
    const minutes = bottleCount * 2;
    timeEarnedEl.textContent = `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  
  showToast('Bottle registered! +2 minutes');
}

// Get current bottle count
export function getBottleCount() {
  return bottleCount;
}