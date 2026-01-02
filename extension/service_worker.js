// service_worker.js
// - Receives messages from content_script
// - Calls backend endpoints (stored in chrome.storage) and polls job status

async function getBackendUrl() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['backendUrl'], (items) => {
      // default to mock server for local dev
      resolve(items.backendUrl || 'http://localhost:9000');
    });
  });
}

function pollJob(backend, jobId, tabId) {
  const check = async () => {
    try {
      const res = await fetch(`${backend}/api/job-status/${jobId}`);
      const data = await res.json();
      // forward status to the tab
      chrome.tabs.sendMessage(tabId, { type: 'job-status', status: data.status, job: data });
      if (data.status === 'done' || data.status === 'error') return;
    } catch (e) {
      console.error('poll error', e);
    }
    setTimeout(check, 2000);
  };
  check();
}

// job subscriptions: job_id -> array of tabIds to notify
const JOB_SUBSCRIPTIONS = {};
let WS_CONN = null;

async function getBackendWs() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['backendWs', 'backendUrl'], (items) => {
      if (items.backendWs) return resolve(items.backendWs);
      const url = items.backendUrl || 'http://localhost:8000';
      const ws = url.replace(/^http/, 'ws') + '/ws';
      resolve(ws);
    });
  });
}

function connectWebsocket() {
  (async () => {
    const wsUrl = await getBackendWs();
    try {
      if (WS_CONN && WS_CONN.readyState === WebSocket.OPEN) return;
      WS_CONN = new WebSocket(wsUrl);
      WS_CONN.onopen = () => console.log('WS connected', wsUrl);
      WS_CONN.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === 'job-update' && msg.job_id) {
            const tabs = JOB_SUBSCRIPTIONS[msg.job_id] || [];
            tabs.forEach(tid => chrome.tabs.sendMessage(tid, { type: 'job-status', status: msg.status, job: msg }));
          }
        } catch (e) { console.error('ws msg parse', e); }
      };
      WS_CONN.onclose = () => { console.log('WS closed, will retry'); setTimeout(connectWebsocket, 3000); };
      WS_CONN.onerror = (e) => { console.error('WS error', e); WS_CONN.close(); };
    } catch (e) { console.error('connect ws failed', e); }
  })();
}

// try establish websocket on startup
connectWebsocket();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!sender.tab) sender.tab = { id: null };
  (async () => {
    const backend = await getBackendUrl();
    try {
      if (message.type === 'generate-outline') {
        const resp = await fetch(`${backend}/api/generate-outline`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(message.payload)
        });
        const data = await resp.json();
        if (data.slides) {
          chrome.tabs.sendMessage(sender.tab.id, { type: 'outline-result', data });
          sendResponse({ ok: true });
        } else if (data.job_id) {
          JOB_SUBSCRIPTIONS[data.job_id] = (JOB_SUBSCRIPTIONS[data.job_id] || []).concat([sender.tab.id]);
          // if websocket present, rely on it; otherwise poll
          if (!WS_CONN || WS_CONN.readyState !== WebSocket.OPEN) pollJob(backend, data.job_id, sender.tab.id);
          sendResponse({ ok: true, job_id: data.job_id });
        } else {
          sendResponse({ ok: false });
        }
      } else if (message.type === 'generate-image') {
        const resp = await fetch(`${backend}/api/generate-image`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(message.payload)
        });
        const data = await resp.json();
        if (data.job_id) {
          JOB_SUBSCRIPTIONS[data.job_id] = (JOB_SUBSCRIPTIONS[data.job_id] || []).concat([sender.tab.id]);
          if (!WS_CONN || WS_CONN.readyState !== WebSocket.OPEN) pollJob(backend, data.job_id, sender.tab.id);
          sendResponse({ ok: true, job_id: data.job_id });
        } else {
          sendResponse({ ok: false });
        }
      }
    } catch (e) {
      console.error('error calling backend', e);
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  // indicate async response
  return true;
});
