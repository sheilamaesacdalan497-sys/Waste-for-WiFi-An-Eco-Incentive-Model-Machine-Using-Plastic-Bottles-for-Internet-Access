export const $ = (id) => document.getElementById(id);

export function openModal(id) {
  const modal = $(id);
  if (modal) modal.classList.add('active');
}

export function closeModal(id) {
  const modal = $(id);
  if (modal) modal.classList.remove('active');
}

export function showToast(text, ms = 2500) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerText = text;
  const container = $('toasts');
  if (!container) return;
  container.appendChild(t);
  setTimeout(() => t.remove(), ms);
}

export function setConnected(flag){ const root = document.querySelector('.app-root'); if(!root) return; root.classList.toggle('connected', !!flag); }
