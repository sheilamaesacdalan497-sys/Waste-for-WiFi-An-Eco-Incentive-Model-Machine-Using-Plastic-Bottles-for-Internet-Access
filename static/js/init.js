import { $, openModal, closeModal, showToast } from './dom.js';
import { registerSession, sendBottle, startPolling, setSessionFromUrl } from './session.js';

document.addEventListener('DOMContentLoaded', ()=>{
  setSessionFromUrl();

  let bottleTimerId = null;
  const TOTAL_SECONDS = 5; // Set to 5 seconds

  const formatCountdown = (sec)=>{
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m} min. ${String(s).padStart(2, '0')} sec.`;
  };

  const resetBottleModal = ()=>{
    if (bottleTimerId) {
      clearInterval(bottleTimerId);
      bottleTimerId = null;
    }
    const countdown = $('bottle-countdown');
    const progress = $('bottle-progress');
    if (countdown) countdown.textContent = formatCountdown(TOTAL_SECONDS);
    if (progress) progress.style.width = '0%';
  };

  const startBottleCountdown = ()=>{
    resetBottleModal();
    let remaining = TOTAL_SECONDS;
    const countdown = $('bottle-countdown');
    const progress = $('bottle-progress');

    bottleTimerId = setInterval(()=>{
      remaining -= 1;
      const elapsed = TOTAL_SECONDS - remaining;
      const pct = Math.min(100, Math.max(0, (elapsed / TOTAL_SECONDS) * 100));

      if (countdown) countdown.textContent = formatCountdown(Math.max(0, remaining));
      if (progress) progress.style.width = `${pct}%`;

      if (remaining <= 0) {
        clearInterval(bottleTimerId);
        bottleTimerId = null;
      }
    }, 1000);
  };

  const regBtn = $('modal-register-btn'); 
  if(regBtn) regBtn.addEventListener('click', async ()=>{ await registerSession(); closeModal('modal-register'); });

  const insertBtn = $('btn-insert-bottle'); 
  if(insertBtn) insertBtn.addEventListener('click', async ()=>{
    openModal('modal-insert-bottle');
    startBottleCountdown();
    await sendBottle();
  });

  // How It Works Modal
  const howBtn = $('btn-howitworks');
  if (howBtn) {
    howBtn.addEventListener('click', () => openModal('modal-howitworks'));
  }

  const howItWorksBtn = $('btn-howitworks'); if(howItWorksBtn) howItWorksBtn.addEventListener('click', ()=>{ openModal('modal-howitworks'); });
  const rateBtn = $('btn-rate');
  if (rateBtn) {
    rateBtn.addEventListener('click', () => {
      window.location.href = '/rate.html';
    });
  }

  document.body.addEventListener('click', (e)=>{
    if(e.target.classList.contains('modal-close')){
      const modal = e.target.closest('.modal'); 
      if(modal) modal.classList.remove('active');
      if (modal && modal.id === 'modal-bottle') resetBottleModal();
    }
    if(e.target.classList && e.target.classList.contains('modal')){
      e.target.classList.remove('active');
      if (e.target.id === 'modal-bottle') resetBottleModal();
    }
  });

  startPolling();
});
