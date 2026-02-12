import { $, openModal, closeModal } from './dom.js';
import { startBottleTimer, stopBottleTimer, registerBottle } from './timer.js';
import { initMockDevPanel } from './mockDevPanel.js';
import {
  getCurrentSessionId,
  setCurrentSessionId,
  activateSession,
  updateButtonStates,
  fetchAndUpdateSession
} from './sessionManager.js';

function attachGuardedButton(buttonId, onAllowed) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;
  
  const checkAndExecute = (e) => {
    const sessionId = getCurrentSessionId();
    if (!sessionId) {
      e.preventDefault();
      e.stopImmediatePropagation?.();
      e.stopPropagation();
      return;
    }
    if (typeof onAllowed === 'function') onAllowed(e);
  };
  
  btn.addEventListener('click', checkAndExecute, { capture: true });
}

// Event: Session created via dev panel
window.addEventListener('session-created', (e) => {
  const id = e?.detail?.session_id;
  if (!id) return;
  setCurrentSessionId(id);
  updateButtonStates({ status: 'awaiting_insertion' });
  fetchAndUpdateSession(id);
});

// Event: Bottle registered (immediate feedback)
window.addEventListener('bottle-registered', (e) => {
  const d = e?.detail ?? {};
  const session_id = d.session_id ?? getCurrentSessionId();
  const bottles = Number(d.bottles ?? 0);
  const seconds = Number(d.seconds ?? 0);
  
  if (!session_id) {
    console.warn('bottle-registered: no session_id');
    return;
  }
  
  activateSession(session_id, bottles, seconds);
});

// Event: Bottles committed (final count)
window.addEventListener('bottles-committed', (e) => {
  const d = e?.detail ?? {};
  const session_id = d.session_id ?? getCurrentSessionId();
  const bottles = Number(d.bottles ?? 0);
  const seconds = Number(d.seconds ?? 0);

  if (!session_id) {
    console.warn('bottles-committed: no session_id');
    return;
  }

  activateSession(session_id, bottles, seconds);
});

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  const currentSessionId = getCurrentSessionId();
  
  // Set initial button states
  updateButtonStates(currentSessionId ? { status: 'awaiting_insertion' } : null);

  // Attach guarded buttons
  attachGuardedButton('btn-insert-bottle', () => {
    const sessionId = getCurrentSessionId();
    if (!sessionId) return;
    openModal('modal-insert-bottle');
    startBottleTimer(sessionId);
  });

  attachGuardedButton('btn-rate', () => {
    openModal('modal-rate');
  });

  // Modal close handlers
  const doneBtn = document.querySelector('.modal-close');
  if (doneBtn) {
    doneBtn.addEventListener('click', () => stopBottleTimer());
  }

  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal');
      if (modal) closeModal(modal.id);
    });
  });

  // Mock bottle button (dev/testing)
  const mockBottleBtn = $('mock-bottle-btn');
  if (mockBottleBtn) {
    mockBottleBtn.addEventListener('click', () => registerBottle());
  }

  // How it works button
  const howBtn = $('btn-howitworks');
  if (howBtn) {
    howBtn.addEventListener('click', () => openModal('modal-howitworks'));
  }

  initMockDevPanel();
});

export { fetchAndUpdateSession };
