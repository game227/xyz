/* XYZ Live WebRTC + chat — barqaror host preview + signaling */
(function () {
  const cfg = window.XYZ_LIVE;
  if (!cfg || !cfg.sessionId) return;

  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${proto}://${location.host}${cfg.wsPath}`;
  const isHost = cfg.role === 'host';
  const localVideo = document.getElementById('live-local');
  const remoteVideo = document.getElementById('live-remote');
  const placeholder = document.getElementById('live-placeholder');
  const chatLog = document.getElementById('live-chat-log');
  const chatForm = document.getElementById('live-chat-form');
  const chatInput = document.getElementById('live-chat-input');

  const pcs = new Map();
  let localStream = null;
  let socket = null;
  let closed = false;
  let reconnectTimer = null;
  let reconnectAttempt = 0;

  const iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ];

  function appendChat(user, text, isTeacher, created) {
    if (!chatLog) return;
    const empty = document.getElementById('chat-empty');
    if (empty) empty.remove();
    const el = document.createElement('div');
    el.className = 'live-chat__item' + (isTeacher ? ' is-teacher' : '');
    el.innerHTML = '<strong></strong><span></span><small></small>';
    el.querySelector('strong').textContent = user;
    el.querySelector('span').textContent = text;
    el.querySelector('small').textContent = created || '';
    chatLog.appendChild(el);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function send(obj) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(obj));
    }
  }

  function attachLocalPreview() {
    if (!localVideo || !localStream) return;
    if (localVideo.srcObject !== localStream) {
      localVideo.srcObject = localStream;
    }
    localVideo.muted = true;
    localVideo.playsInline = true;
    const play = () => localVideo.play().catch(() => {});
    play();
    // Brauzer ba’zan pauza qiladi — qayta o‘ynatamiz
    localVideo.onpause = () => {
      if (!closed && localStream) play();
    };
  }

  async function ensureLocal() {
    if (localStream && localStream.getTracks().some((t) => t.readyState === 'live')) {
      attachLocalPreview();
      return localStream;
    }
    localStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: true,
    });
    localStream.getTracks().forEach((track) => {
      track.onended = () => {
        console.warn('Live track ended:', track.kind);
      };
    });
    attachLocalPreview();
    return localStream;
  }

  function closePC(peerId) {
    const pc = pcs.get(peerId);
    if (!pc) return;
    try { pc.close(); } catch (_) { /* ignore */ }
    pcs.delete(peerId);
  }

  function createPC(peerId) {
    if (pcs.has(peerId)) return pcs.get(peerId);
    const pc = new RTCPeerConnection({ iceServers });
    pcs.set(peerId, pc);

    pc.onicecandidate = (e) => {
      if (e.candidate) {
        send({ type: 'ice', to: peerId, candidate: e.candidate });
      }
    };

    pc.ontrack = (e) => {
      if (!remoteVideo) return;
      const stream = e.streams[0] || new MediaStream([e.track]);
      remoteVideo.srcObject = stream;
      remoteVideo.play().catch(() => {});
      if (placeholder) placeholder.classList.add('d-none');
    };

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState;
      if (state === 'failed') {
        closePC(peerId);
      } else if (state === 'closed') {
        pcs.delete(peerId);
      }
      // 'disconnected' — vaqtinchalik, PC ni o‘chirmaymiz (kamera/stream saqlansin)
    };

    return pc;
  }

  async function addLocalTracks(pc) {
    const stream = await ensureLocal();
    const senders = pc.getSenders();
    stream.getTracks().forEach((track) => {
      const already = senders.some((s) => s.track && s.track.id === track.id);
      if (!already) pc.addTrack(track, stream);
    });
  }

  async function hostOfferTo(peerId) {
    if (!isHost || peerId === (socket && socket._channelHint)) return;
    let pc = pcs.get(peerId);
    if (pc && ['connected', 'connecting'].includes(pc.connectionState)) {
      return;
    }
    if (pc && pc.signalingState !== 'stable') {
      closePC(peerId);
    }
    pc = createPC(peerId);
    await addLocalTracks(pc);
    const offer = await pc.createOffer({ offerToReceiveAudio: false, offerToReceiveVideo: false });
    await pc.setLocalDescription(offer);
    send({ type: 'offer', to: peerId, sdp: pc.localDescription });
  }

  async function handleOffer(from, sdp) {
    if (isHost) return;
    closePC(from);
    const pc = createPC(from);
    await pc.setRemoteDescription(sdp);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    send({ type: 'answer', to: from, sdp: pc.localDescription });
  }

  async function handleAnswer(from, sdp) {
    const pc = pcs.get(from);
    if (!pc) return;
    if (pc.signalingState === 'have-local-offer') {
      await pc.setRemoteDescription(sdp);
    }
  }

  async function handleIce(from, candidate) {
    const pc = pcs.get(from);
    if (!pc || !candidate) return;
    try {
      await pc.addIceCandidate(candidate);
    } catch (_) { /* ignore early ICE */ }
  }

  function scheduleReconnect() {
    if (closed || reconnectTimer) return;
    const delay = Math.min(8000, 1000 + reconnectAttempt * 1000);
    reconnectAttempt += 1;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWS();
    }, delay);
  }

  function connectWS() {
    if (closed) return;
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    socket = new WebSocket(wsUrl);
    socket.onopen = async () => {
      reconnectAttempt = 0;
      if (isHost) {
        try {
          await ensureLocal();
          send({ type: 'host-ready' });
        } catch (err) {
          console.error(err);
          alert('Kamera/mikrofon ruxsati kerak. HTTPS yoki localhost da oching.');
        }
      } else {
        send({ type: 'viewer-ready' });
      }
    };
    socket.onmessage = async (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (_) { return; }
      const from = data.from;
      if (data.type === 'chat') {
        appendChat(data.user, data.text, data.is_teacher, data.created);
        return;
      }
      if (data.type === 'error') {
        if (data.message) alert(data.message);
        return;
      }
      try {
        if (isHost && (data.type === 'peer-join' || data.type === 'viewer-ready') && from) {
          await hostOfferTo(from);
          return;
        }
        if (!isHost && data.type === 'host-ready') {
          send({ type: 'viewer-ready' });
          return;
        }
        if (data.type === 'offer' && data.sdp && from) {
          await handleOffer(from, data.sdp);
        } else if (data.type === 'answer' && data.sdp && from) {
          await handleAnswer(from, data.sdp);
        } else if (data.type === 'ice' && data.candidate && from) {
          await handleIce(from, data.candidate);
        } else if (data.type === 'peer-leave' && from) {
          closePC(from);
          if (!isHost && remoteVideo && pcs.size === 0) {
            remoteVideo.srcObject = null;
            if (placeholder) placeholder.classList.remove('d-none');
          }
        }
      } catch (err) {
        console.error('Live signal error', err);
      }
    };
    socket.onclose = () => {
      if (!closed) scheduleReconnect();
    };
    socket.onerror = () => {
      try { socket.close(); } catch (_) { /* ignore */ }
    };
  }

  if (chatForm && cfg.canChat) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = (chatInput.value || '').trim();
      if (!text) return;
      send({ type: 'chat', text });
      chatInput.value = '';
    });
  }

  window.addEventListener('beforeunload', () => {
    closed = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    pcs.forEach((pc) => { try { pc.close(); } catch (_) { /* ignore */ } });
    pcs.clear();
    // Local stream ni beforeunload da to‘xtatmaymiz — brauzer o‘zi yopadi.
    // Host preview barqarorligi uchun track.stop() chaqirilmaydi.
  });

  // Sahifa ko‘rinib turganda preview ni qayta yoqish
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && isHost) attachLocalPreview();
  });

  connectWS();
})();
