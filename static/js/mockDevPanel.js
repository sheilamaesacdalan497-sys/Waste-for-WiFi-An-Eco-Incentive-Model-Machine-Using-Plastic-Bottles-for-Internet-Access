/**
 * Mock Dev Panel - Draggable developer controls
 */

let isDragging = false;
let currentX;
let currentY;
let initialX;
let initialY;
let xOffset = 0;
let yOffset = 0;

export function initMockDevPanel() {
  const panel = document.getElementById('mock-dev-panel');
  const dragHandle = document.getElementById('mock-drag-handle');
  const toggleBtn = document.getElementById('mock-toggle-btn');
  const mockBody = document.getElementById('mock-body');
  const createSessionBtn = document.getElementById('mock-create-session-btn');
  const bottleInsertBtn = document.getElementById('mock-bottle-insert-btn');
  const sessionInfo = document.getElementById('mock-session-info');

  if (!panel) return;

  // Make panel draggable
  dragHandle.addEventListener('mousedown', dragStart);
  document.addEventListener('mousemove', drag);
  document.addEventListener('mouseup', dragEnd);

  // Toggle collapse
  toggleBtn.addEventListener('click', () => {
    mockBody.classList.toggle('collapsed');
    toggleBtn.textContent = mockBody.classList.contains('collapsed') ? '+' : '−';
  });

  // Mock create session
  createSessionBtn.addEventListener('click', async () => {
    try {
      const mac = `AA:BB:CC:DD:EE:${Math.random().toString(16).substr(2, 2).toUpperCase()}`;
      const ip = `192.168.1.${Math.floor(Math.random() * 200 + 10)}`;
      
      const response = await fetch('/api/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mac_address: mac, ip_address: ip })
      });

      const data = await response.json();
      
      if (response.ok) {
        sessionInfo.innerHTML = `✅ Session ID: ${data.session_id}<br>MAC: ${mac}<br>Status: ${data.status}`;
        showToast('Session created successfully', 'success');
        
        // Store session ID globally for other mock actions
        window.mockSessionId = data.session_id;
        
        // Store in localStorage so main UI can access it
        localStorage.setItem('session_id', data.session_id);
        localStorage.setItem('session_status', data.status);
        
        // Trigger session check to update main UI
        window.dispatchEvent(new CustomEvent('session-created', { 
          detail: { session_id: data.session_id, status: data.status } 
        }));
        
        // Refresh UI
        if (window.checkSession) window.checkSession();
      } else {
        sessionInfo.textContent = `❌ Error: ${data.error}`;
        showToast('Failed to create session', 'error');
      }
    } catch (error) {
      console.error('Mock create session error:', error);
      sessionInfo.textContent = `❌ ${error.message}`;
      showToast('Connection error', 'error');
    }
  });

  // Mock bottle insert
  bottleInsertBtn.addEventListener('click', async () => {
    if (!window.mockSessionId) {
      showToast('Create a session first', 'error');
      return;
    }

    try {
      const response = await fetch('/api/bottle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: window.mockSessionId })
      });

      const data = await response.json();
      
      if (response.ok) {
        sessionInfo.innerHTML = `✅ Session ID: ${window.mockSessionId}<br>Bottles: ${data.bottles_inserted}<br>Time: ${data.minutes_earned} min`;
        showToast(`Bottle inserted! +${data.minutes_earned} min`, 'success');
        
        // Update UI counters if modal is open
        const bottleCount = document.getElementById('bottle-count');
        const timeEarned = document.getElementById('time-earned');
        if (bottleCount) bottleCount.textContent = data.bottles_inserted;
        if (timeEarned) timeEarned.textContent = `${data.minutes_earned} minutes`;
      } else {
        showToast(data.error || 'Failed to insert bottle', 'error');
      }
    } catch (error) {
      console.error('Mock bottle insert error:', error);
      showToast('Connection error', 'error');
    }
  });

  function dragStart(e) {
    initialX = e.clientX - xOffset;
    initialY = e.clientY - yOffset;

    if (e.target === dragHandle || dragHandle.contains(e.target)) {
      isDragging = true;
      panel.style.cursor = 'grabbing';
    }
  }

  function drag(e) {
    if (isDragging) {
      e.preventDefault();
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;

      xOffset = currentX;
      yOffset = currentY;

      setTranslate(currentX, currentY, panel);
    }
  }

  function dragEnd(e) {
    initialX = currentX;
    initialY = currentY;
    isDragging = false;
    panel.style.cursor = 'default';
  }

  function setTranslate(xPos, yPos, el) {
    el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
  }
}

function showToast(message, type = 'info') {
  // Reuse existing toast system
  if (window.showToast) {
    window.showToast(message, type);
  } else {
    console.log(`[TOAST ${type}]`, message);
  }
}