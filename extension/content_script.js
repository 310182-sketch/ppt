/*
  content_script.js
  - Injects a floating button and simple panel into Canva pages.
  - Sends generate requests to the background service worker.
  - Receives results and displays a basic preview / instructions.
*/

function waitForCanvasContainer(timeout = 10000) {
  return new Promise((resolve) => {
    const start = Date.now();
    const iv = setInterval(() => {
      // heuristic selector: look for main app container
      const container = document.querySelector('[data-test-id="editor-canvas"]') || document.querySelector('body');
      if (container) {
        clearInterval(iv);
        resolve(container);
      }
      if (Date.now() - start > timeout) {
        clearInterval(iv);
        resolve(document.body);
      }
    }, 300);
  });
}

function createUI() {
  if (document.getElementById('ai-ppt-extension-root')) return;
  const root = document.createElement('div');
  root.id = 'ai-ppt-extension-root';
  root.innerHTML = `
    <style>
      #ai-ppt-floating { position: fixed; right: 20px; bottom: 20px; z-index: 99999; }
      #ai-ppt-panel { width: 320px; background: white; border: 1px solid #ddd; padding: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
      #ai-ppt-panel h4 { margin: 0 0 8px 0; }
      #ai-ppt-panel input, #ai-ppt-panel textarea, #ai-ppt-panel select { width: 100%; box-sizing: border-box; margin-bottom:8px; }
      #ai-ppt-result { max-height: 200px; overflow:auto; }
    </style>
    <div id="ai-ppt-floating">
      <button id="ai-ppt-open">AI PPT</button>
      <div id="ai-ppt-panel" style="display:none">
        <h4>生成大綱</h4>
        <input id="ai-title" placeholder="標題" />
        <input id="ai-audience" placeholder="聽眾 (選填)" />
        <select id="ai-length"><option value="5">5 頁</option><option value="10">10 頁</option></select>
        <button id="ai-generate-outline">開始</button>
        <div id="ai-ppt-result"></div>
      </div>
    </div>
  `;
  document.documentElement.appendChild(root);

  const btn = document.getElementById('ai-ppt-open');
  const panel = document.getElementById('ai-ppt-panel');
  btn.addEventListener('click', () => { panel.style.display = panel.style.display === 'none' ? 'block' : 'none'; });

  document.getElementById('ai-generate-outline').addEventListener('click', async () => {
    const title = document.getElementById('ai-title').value || '簡短標題';
    const audience = document.getElementById('ai-audience').value || '';
    const length = parseInt(document.getElementById('ai-length').value || '5', 10);
    // send message to background to call backend
    chrome.runtime.sendMessage({ type: 'generate-outline', payload: { title, audience, length, style: 'default' } }, (resp) => {
      // immediate response may be undefined; background will send result later
      console.log('generate-outline message sent', resp);
      showStatus('已送出生成請求，稍候...');
    });
  });

  // quick image generation + insert button for testing automatic upload
  const imgBtn = document.createElement('button');
  imgBtn.innerText = '生成示例圖片並插入';
  imgBtn.addEventListener('click', () => {
    const prompt = '示例圖: 一個簡潔的科技插畫';
    chrome.runtime.sendMessage({ type: 'generate-image', payload: { prompt, size: '800x600', style: 'flat' } }, (resp) => {
      showStatus('圖片生成中...');
    });
  });
  panel.appendChild(imgBtn);

  function showStatus(html) {
    const r = document.getElementById('ai-ppt-result');
    r.innerHTML = html;
  }

  // receive results from background
  chrome.runtime.onMessage.addListener((message, sender) => {
    if (message.type === 'outline-result') {
      const slides = message.data.slides || [];
      const html = slides.map(s => `<div><strong>${s.title}</strong><ul>${(s.bullets||[]).map(b=>`<li>${b}</li>`).join('')}</ul></div>`).join('');
      showStatus(html);
      // optionally offer insert/upload actions here
    }
    if (message.type === 'job-status') {
      showStatus(`<div>狀態：${message.status}</div>`);
      // if job contains image_url, try auto-insert
      const job = message.job || {};
      if (job.result && job.result.image_url) {
        attemptInsertImage(job.result.image_url);
      } else if (job.image_url) {
        attemptInsertImage(job.image_url);
      }
    }
  });

  async function attemptInsertImage(imageUrl) {
    try {
      const r = await fetch(imageUrl.replace(/^file:\/\//, ''));
      const blob = await r.blob();
      const fname = 'ai_image.png';
      const file = new File([blob], fname, { type: blob.type });
      // Attempt 1: find file input and set files via DataTransfer
      const fileInputs = Array.from(document.querySelectorAll('input[type=file]'));
      if (fileInputs.length > 0) {
        const input = fileInputs[0];
        const dt = new DataTransfer();
        dt.items.add(file);
        try {
          Object.defineProperty(input, 'files', { value: dt.files });
        } catch (e) {
          // fallback: use dispatchEvent with DataTransfer on drop target
        }
        const ev = new Event('change', { bubbles: true });
        input.dispatchEvent(ev);
        showStatus('嘗試自動上傳至 Canva（使用 file input）');
        return;
      }

      // Attempt 2: simulate drop on canvas
      const canvas = document.querySelector('[data-test-id="editor-canvas"]') || document.body;
      const dt = new DataTransfer();
      dt.items.add(file);
      const dropEvent = new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true });
      canvas.dispatchEvent(dropEvent);
      showStatus('嘗試模擬拖放上傳（若失敗請手動上傳）');
      return;
    } catch (e) {
      console.error('insert image failed', e);
      showStatus('自動插入失敗，請下載後手動上傳');
      // provide download link
      const rdiv = document.getElementById('ai-ppt-result');
      rdiv.innerHTML += `<div><a href="${imageUrl}" target="_blank" download>下載圖片</a></div>`;
    }
  }
}

(async function init(){
  const container = await waitForCanvasContainer();
  createUI(container);
})();
