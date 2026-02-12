export const $ = (id) => document.getElementById(id);

export function openModal(id) {
  const modal = $(id);
  if (modal) modal.classList.add('active');
}

export function closeModal(id) {
  const modal = $(id);
  if (modal) modal.classList.remove('active');
}

export function showToast(message, type = 'info') {
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerText = message;
  const container = $('toasts');
  if (!container) return;
  container.appendChild(t);
  setTimeout(() => t.remove(), 2500);
}

// expose to global so other modules/legacy handlers can call it without extra toast code
window.showToast = showToast;

export function setConnected(flag){ const root = document.querySelector('.app-root'); if(!root) return; root.classList.toggle('connected', !!flag); }
