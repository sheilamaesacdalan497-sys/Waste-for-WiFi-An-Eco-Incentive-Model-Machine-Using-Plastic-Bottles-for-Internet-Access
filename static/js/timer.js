import { $ , closeModal } from './dom.js';

const BOTTLE_TIMER_DURATION = 180; // seconds (3 minutes)
const SECONDS_PER_BOTTLE = 120;
let bottleTimerInterval = null;
let bottleTimeRemaining = BOTTLE_TIMER_DURATION;
let bottleCount = 0;
let currentSessionId = null;

export function startBottleTimer(sessionId) {
  // ensure a session id is present (use provided -> mock -> generate)
  currentSessionId = sessionId ?? window.mockSessionId ?? `mock-${Date.now()}`;
  bottleTimeRemaining = BOTTLE_TIMER_DURATION;
  bottleCount = 0;

  const progressBar = $('bottle-progress');
  const countdownEl = $('bottle-countdown');
  const bottleCountEl = $('bottle-count');
  const timeEarnedEl = $('time-earned');

  if (bottleCountEl) bottleCountEl.textContent = String(bottleCount);
  if (timeEarnedEl) timeEarnedEl.textContent = `0 minutes`;
  if (countdownEl) countdownEl.textContent = formatSeconds(bottleTimeRemaining);
  if (progressBar) progressBar.style.width = '100%'; // start full

  if (bottleTimerInterval) {
    clearInterval(bottleTimerInterval);
    bottleTimerInterval = null;
  }

  bottleTimerInterval = setInterval(() => {
    bottleTimeRemaining--;
    if (countdownEl) countdownEl.textContent = formatSeconds(bottleTimeRemaining);
    if (progressBar) progressBar.style.width = `${Math.max(0, Math.round((bottleTimeRemaining / BOTTLE_TIMER_DURATION) * 100))}%`;
    if (bottleTimeRemaining <= 0) {
      clearInterval(bottleTimerInterval);
      bottleTimerInterval = null;
      handleTimerEnd();
    }
  }, 1000);
}

export function stopBottleTimer() {
  if (bottleTimerInterval) {
    clearInterval(bottleTimerInterval);
    bottleTimerInterval = null;
  }
  handleTimerEnd();
}

async function handleTimerEnd() {
  try { closeModal('modal-insert-bottle'); } catch (e) {}
  const secondsEarned = bottleCount * SECONDS_PER_BOTTLE;

  // dispatch final commit
  window.dispatchEvent(new CustomEvent('bottles-committed', {
    detail: {
      session_id: currentSessionId,
      bottles: bottleCount,
      seconds: secondsEarned
    }
  }));

  // reset
  bottleCount = 0;
  bottleTimeRemaining = BOTTLE_TIMER_DURATION;
}

// Called when a bottle is inserted (mock or real sensor)
export function registerBottle() {
  // ensure session id exists
  currentSessionId = currentSessionId ?? window.mockSessionId ?? `mock-${Date.now()}`;
  bottleCount++;
  const bottleCountEl = $('bottle-count');
  const timeEarnedEl = $('time-earned');
  if (bottleCountEl) bottleCountEl.textContent = String(bottleCount);
  if (timeEarnedEl) timeEarnedEl.textContent = `${Math.floor((bottleCount * SECONDS_PER_BOTTLE) / 60)} minutes`;

  // notify UI immediately so timer-card/status can show
  window.dispatchEvent(new CustomEvent('bottle-registered', {
    detail: {
      session_id: currentSessionId,
      bottles: bottleCount,
      seconds: bottleCount * SECONDS_PER_BOTTLE
    }
  }));
}

// helpers
function formatSeconds(sec) {
  if (sec <= 0) return '0 min 00 sec';
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m} min. ${String(s).padStart(2, '0')} sec.`;
}

export function getBottleCount() { return bottleCount; }
export function getCurrentSessionId() { return currentSessionId; }