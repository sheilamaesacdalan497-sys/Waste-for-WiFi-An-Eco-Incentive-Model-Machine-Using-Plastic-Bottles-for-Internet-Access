import { $, showToast, setConnected } from './dom.js';

let sessionId = null;

export function getSessionId(){ return sessionId; }

export async function registerSession(){
  try{
    const res = await fetch('/register', {method:'POST', headers:{'X-Requested-With':'XMLHttpRequest'}});
    const data = await res.json();
    sessionId = data.session_id;
    setConnected(true);
    showToast('Session created');
    return sessionId;
  }catch(e){ console.error(e); showToast('Registration failed'); throw e; }
}

export async function sendBottle(){
  const sid = sessionStorage.getItem('econet_session');
  if (!sid) {
    showToast('No session found. Please reconnect.');
    return;
  }
  
  try {
    const res = await fetch('/api/bottle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sid })
    });
    
    if (res.ok) {
      const data = await res.json();
      showToast(`+${data.minutes_added} minutes added!`);
      
      // Refresh timer with updated session
      updateTimer(data.session);
    } else {
      showToast('Failed to register bottle.');
    }
  } catch (err) {
    showToast('Network error.');
  }
}

export async function pollStatus(){
  if(!sessionId) return;
  try{
    const res = await fetch(`/api/session/${sessionId}/status`);
    const data = await res.json();
    if($('ip')) $('ip').innerText = data.ip || '-';
    if($('mac')) $('mac').innerText = data.mac || '-';
    if($('bottles')) $('bottles').innerText = data.bottles || 0;
    if($('timer')){
      $('timer').setAttribute('data-end', data.end || 0);
      $('timer').setAttribute('data-duration', data.duration || 0);
      $('timer').innerText = formatTime(data);
    }
    setConnected(data.status === 'active');
    return data;
  }catch(e){ console.error('pollStatus', e); }
}

function formatTime(data){
  if(!data || data.status !== 'active') return '-- HR. -- MIN. -- SEC';
  const now = Math.floor(Date.now()/1000);
  const end = data.end || 0;
  let diff = Math.max(0, end - now);
  const hrs = Math.floor(diff/3600); diff%=3600; const mins = Math.floor(diff/60); const secs = diff%60;
  return `${hrs} HR. ${mins} MIN. ${secs} SEC`;
}

export function startPolling(intervalMs=3000){
  setInterval(()=>{ if(sessionId) pollStatus(); }, intervalMs);
}

export function setSessionFromUrl(){
  const path = window.location.pathname.split('/');
  if(path.length >= 3 && path[1] === 'rating'){ sessionId = path[2]; }
}
