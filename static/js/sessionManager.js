import { $, setConnected } from './dom.js';
import { formatTime, getCurrentTimestamp } from './utils.js';

let sessionTimerInterval = null;
let currentSessionId = localStorage.getItem('session_id') || window.mockSessionId || null;
let pendingSessionData = null; // Store session data before timer starts

export function getCurrentSessionId() {
  return currentSessionId;
}

export function setCurrentSessionId(id) {
  currentSessionId = id ? String(id) : null;
  if (id) {
    localStorage.setItem('session_id', id);
  } else {
    localStorage.removeItem('session_id');
  }
}

export function activateSession(session_id, bottles = 0, seconds = 0) {
  if (!session_id) {
    console.warn('activateSession: missing session_id');
    return;
  }

  setCurrentSessionId(session_id);
  
  // Update connection status UI
  updateConnectionStatus(true);

  // Build session data object
  const now = Math.floor(Date.now() / 1000);
  const sessionData = {
    id: Number(currentSessionId),
    status: bottles > 0 ? 'active' : 'awaiting_insertion',
    bottles_inserted: bottles,
    session_start: now,
    session_end: now + (seconds || 0)
  };

  // Store pending data but don't show timer yet
  pendingSessionData = sessionData;
  
  // Only update button states, don't start timer yet
  updateButtonStates(sessionData);
  
  console.log('Session activated (pending timer start):', sessionData);
}

// Call this when modal closes or timer ends
export function startSessionTimer() {
  if (!pendingSessionData) {
    console.warn('startSessionTimer: no pending session data');
    return;
  }

  // Now show and start the timer countdown
  updateSessionTimer(pendingSessionData);
  pendingSessionData = null; // Clear pending data
}

export function updateConnectionStatus(connected) {
  try {
    setConnected(connected);
    
    const statusPill = document.querySelector('.status-pill');
    const connDot = document.getElementById('connection-dot');
    const connLabel = document.getElementById('connected-label');
    
    if (statusPill) {
      if (connected) {
        statusPill.classList.add('connected');
      } else {
        statusPill.classList.remove('connected');
      }
    }
    
    if (connDot) {
      connDot.style.background = connected ? '#27ae60' : '#c4c4c4';
    }
    
    if (connLabel) {
      connLabel.textContent = connected ? 'Connected' : 'Disconnected';
    }
  } catch (err) {
    console.error('updateConnectionStatus error', err);
  }
}

export function updateSessionTimer(sessionData) {
  const timerCard = $('timer-card');
  const timerEl = $('timer');

  if (!timerCard || !timerEl) {
    console.warn('Timer elements not found in DOM');
    return;
  }

  const now = getCurrentTimestamp();
  
  // Hide timer if session is not active or has no end time
  if (!sessionData || sessionData.status !== 'active' || !sessionData.session_end || sessionData.session_end <= now) {
    timerCard.classList.remove('active');
    timerCard.style.display = 'none';
    if (sessionTimerInterval) {
      clearInterval(sessionTimerInterval);
      sessionTimerInterval = null;
    }
    return;
  }

  // Show timer card
  timerCard.classList.add('active');
  timerCard.style.display = 'block';

  let remaining = sessionData.session_end - now;
  timerEl.textContent = formatTime(Math.max(0, remaining));

  // Start countdown if not already running
  if (sessionTimerInterval) return;
  
  sessionTimerInterval = setInterval(async () => {
    remaining--;
    if (remaining <= 0) {
      clearInterval(sessionTimerInterval);
      sessionTimerInterval = null;
      timerEl.textContent = 'Expired';
      await expireSession(currentSessionId);
      updateConnectionStatus(false);
      updateButtonStates({ status: 'expired' });
      timerCard.classList.remove('active');
      timerCard.style.display = 'none';
    } else {
      timerEl.textContent = formatTime(remaining);
    }
  }, 1000);
}

export function updateButtonStates(sessionData) {
  const insertBtn = $('btn-insert-bottle');
  const rateBtn = $('btn-rate');

  if (!sessionData) {
    if (insertBtn) insertBtn.disabled = true;
    if (rateBtn) rateBtn.disabled = true;
    return;
  }

  switch (sessionData.status) {
    case 'awaiting_insertion':
      if (insertBtn) insertBtn.disabled = false;
      if (rateBtn) rateBtn.disabled = true;
      break;
    case 'inserting':
      if (insertBtn) insertBtn.disabled = true;
      if (rateBtn) rateBtn.disabled = true;
      break;
    case 'active':
      if (insertBtn) insertBtn.disabled = false;
      if (rateBtn) rateBtn.disabled = false;
      break;
    default:
      if (insertBtn) insertBtn.disabled = true;
      if (rateBtn) rateBtn.disabled = true;
  }
}

async function expireSession(sessionId) {
  if (!sessionId) return;
  try {
    await fetch(`/api/session/${sessionId}/expire`, { method: 'POST' });
    setCurrentSessionId(null);
  } catch (err) {
    console.error('expireSession error', err);
  }
}

export async function fetchAndUpdateSession(sessionId) {
  try {
    const res = await fetch(`/api/session/${sessionId}/status`);
    if (!res.ok) return;
    const sessionData = await res.json();
    setCurrentSessionId(sessionId);
    updateSessionTimer(sessionData);
    updateButtonStates(sessionData);
    updateConnectionStatus(sessionData.status === 'active');
  } catch (err) {
    console.error('fetchAndUpdateSession error', err);
  }
}