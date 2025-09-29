(function () {
  const creativeEl = document.getElementById('messages-creative');
  const historianEl = document.getElementById('messages-historian');
  const formEl = document.getElementById('composer-form');
  const inputEl = document.getElementById('input');
  function createAnnotationElement(text, labelOverride) {
    const wrapper = document.createElement('div');
    wrapper.className = 'annotation';
    const header = document.createElement('div');
    header.className = 'annotation-header';
    header.textContent = labelOverride || 'Historian — Comment';
    const body = document.createElement('div');
    body.className = 'annotation-body';
    body.textContent = text;
    wrapper.appendChild(header);
    wrapper.appendChild(body);
    return wrapper;
  }
  function createMessageElement(role, text, labelOverride) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? 'U' : 'A';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const roleEl = document.createElement('span');
    roleEl.className = 'role';
    if (labelOverride) {
      roleEl.textContent = labelOverride;
    } else {
      roleEl.textContent = role === 'user' ? 'You' : 'Assistant';
    }
    const textEl = document.createElement('div');
    textEl.className = 'text';
    textEl.textContent = text;
    bubble.appendChild(roleEl);
    bubble.appendChild(textEl);
    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    return wrapper;
  }
  function ensureEmptyState() {
    if (!creativeEl.children.length) {
      const empty = document.createElement('div');
      empty.className = 'empty-hint';
      empty.textContent = 'Start a conversation';
      creativeEl.appendChild(empty);
    }
    if (!historianEl.children.length) {
      const empty = document.createElement('div');
      empty.className = 'empty-hint';
      empty.textContent = '—';
      historianEl.appendChild(empty);
    }
  }
  function removeEmptyState() {
    const hints = document.querySelectorAll('.empty-hint');
    hints.forEach(h => h.remove());
  }
  function scrollToBottom() {
    creativeEl.scrollTo({ top: creativeEl.scrollHeight, behavior: 'smooth' });
    historianEl.scrollTo({ top: historianEl.scrollHeight, behavior: 'smooth' });
  }
  function autogrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }
  async function callStream(userText, { onCreativeDelta, onCreativeDone, onHistorianDelta, onHistorianDone, onEvidence, onResearchDone, onError }) {
    const res = await fetch('/api/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText })
    });
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Request failed: ${res.status}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sepIndex;
      while ((sepIndex = buffer.indexOf('\n\n')) >= 0) {
        const rawEvent = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const lines = rawEvent.split('\n');
        let eventType = 'message';
        let dataStr = '';
        for (const line of lines) {
          if (line.startsWith('event:')) eventType = line.slice(6).trim();
          if (line.startsWith('data:')) dataStr += line.slice(5).trim();
        }
        if (!dataStr) continue;
        try {
          const data = JSON.parse(dataStr);
          if (eventType === 'creative') onCreativeDelta && onCreativeDelta(data.delta || '');
          else if (eventType === 'creative_done') onCreativeDone && onCreativeDone(data.text || '');
          else if (eventType === 'evidence') onEvidence && onEvidence(data);
          else if (eventType === 'research_done') onResearchDone && onResearchDone(data);
          else if (eventType === 'historian') onHistorianDelta && onHistorianDelta(data.delta || '');
          else if (eventType === 'historian_done') onHistorianDone && onHistorianDone();
          else if (eventType === 'error') onError && onError(data);
        } catch (e) {
          console.error('Bad SSE data', e);
        }
      }
    }
  }
  async function handleSubmit(event) {
    event.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;
    removeEmptyState();
    const userMsgLeft = createMessageElement('user', text);
    creativeEl.appendChild(userMsgLeft);
    scrollToBottom();
    inputEl.value = '';
    autogrow(inputEl);
    const creativeMsg = createMessageElement('assistant', '', 'Assistant — Creative');
    const creativeTextEl = creativeMsg.querySelector('.text');
    creativeTextEl.textContent = '';
    creativeEl.appendChild(creativeMsg);
    const historianNote = createAnnotationElement('', 'Historian — Comment');
    const historianTextEl = historianNote.querySelector('.annotation-body');
    historianTextEl.textContent = '';
    historianEl.appendChild(historianNote);
    // Evidence container
    const evidenceWrapper = document.createElement('div');
    evidenceWrapper.className = 'annotation';
    const evidenceHeader = document.createElement('div');
    evidenceHeader.className = 'annotation-header';
    evidenceHeader.textContent = 'Research — Evidence';
    const evidenceBody = document.createElement('div');
    evidenceBody.className = 'annotation-body';
    evidenceWrapper.appendChild(evidenceHeader);
    evidenceWrapper.appendChild(evidenceBody);
    historianEl.appendChild(evidenceWrapper);
    scrollToBottom();
    
    try {
      await callStream(text, {
        onCreativeDelta: (d) => { creativeTextEl.textContent += d; scrollToBottom(); },
        onCreativeDone: () => {},
        onEvidence: (ev) => {
          const t = (ev && ev.title) ? ev.title : 'Untitled';
          const u = (ev && ev.url) ? ev.url : '';
          const s = (ev && ev.snippet) ? ev.snippet : '';
          const line = document.createElement('div');
          line.className = 'evidence-line';
          const a = document.createElement('a');
          a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer';
          a.textContent = t;
          const snip = document.createElement('div');
          snip.className = 'evidence-snippet';
          snip.textContent = s;
          line.appendChild(a);
          line.appendChild(snip);
          evidenceBody.appendChild(line);
          scrollToBottom();
        },
        onResearchDone: (info) => {
          const meta = document.createElement('div');
          meta.className = 'evidence-meta';
          meta.textContent = `Found: ${(info && typeof info.count === 'number') ? info.count : 0}`;
          evidenceBody.appendChild(meta);
          scrollToBottom();
        },
        onHistorianDelta: (d) => { historianTextEl.textContent += d; scrollToBottom(); },
        onHistorianDone: () => {},
        onError: (err) => { creativeTextEl.textContent = 'Error'; historianTextEl.textContent = 'Error'; console.error(err); }
      });
    } catch (e) {
      creativeTextEl.textContent = 'Error getting response';
      historianTextEl.textContent = 'Error getting response';
      console.error(e);
    }
    scrollToBottom();
  }
  formEl.addEventListener('submit', handleSubmit);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      formEl.requestSubmit();
    }
  });
  inputEl.addEventListener('input', () => autogrow(inputEl));
  // Initialize
  ensureEmptyState();
  autogrow(inputEl);
})();