/* XYZ Live WebRTC + chat — TURN, ICE queue, autoplay-safe remote video */
(function () {
  const cfg = window.XYZ_LIVE;
  if (!cfg || !cfg.sessionId) return;

  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${proto}://${location.host}${cfg.wsPath}`;
  const isHost = cfg.role === 'host';
  const localVideo = document.getElementById('live-local');
  const remoteVideo = document.getElementById('live-remote');
  const placeholder = document.getElementById('live-placeholder');
  const unmuteBtn = document.getElementById('live-unmute');
  const chatLog = document.getElementById('live-chat-log');
  const chatForm = document.getElementById('live-chat-form');
  const chatInput = document.getElementById('live-chat-input');

  const pcs = new Map();
  const iceQueues = new Map();
  const offering = new Set();
  let localStream = null;
  let socket = null;
  let closed = false;
  let reconnectTimer = null;
  let reconnectAttempt = 0;

  // STUN + ochiq TURN — turli NAT orqasidagi studentlar uchun
  const iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    {
      urls: [
        'turn:openrelay.metered.ca:80',
        'turn:openrelay.metered.ca:443',
        'turn:openrelay.metered.ca:443?transport=tcp',
      ],
      username: 'openrelayproject',
      credential: 'openrelayproject',
    },
  ];

  function setPlaceholder(text, show) {
    if (!placeholder) return;
    if (typeof text === 'string' && text) placeholder.textContent = text;
    placeholder.classList.toggle('d-none', !show);
  }

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
      track.onended = () => console.warn('Live track ended:', track.kind);
    });
    attachLocalPreview();
    return localStream;
  }

  function closePC(peerId) {
    const pc = pcs.get(peerId);
    if (pc) {
      try { pc.close(); } catch (_) { /* ignore */ }
      pcs.delete(peerId);
    }
    iceQueues.delete(peerId);
    offering.delete(peerId);
  }

  async function flushIce(peerId) {
    const pc = pcs.get(peerId);
    const queue = iceQueues.get(peerId);
    if (!pc || !queue || !pc.remoteDescription) return;
    while (queue.length) {
      const candidate = queue.shift();
      try {
        await pc.addIceCandidate(candidate);
      } catch (_) { /* ignore bad/early ICE */ }
    }
  }

  function attachRemoteStream(stream) {
    if (!remoteVideo || !stream) return;
    remoteVideo.srcObject = stream;
    remoteVideo.playsInline = true;
    // Autoplay siyosati: avval muted, keyin foydalanuvchi ovoz yoqadi
    remoteVideo.muted = true;
    const tryPlay = () => {
      remoteVideo.play()
        .then(() => {
          setPlaceholder('', false);
          if (unmuteBtn) unmuteBtn.hidden = false;
        })
        .catch(() => {
          setPlaceholder('Videoni bosib ijro eting', true);
          remoteVideo.addEventListener('click', () => {
            remoteVideo.play().then(() => setPlaceholder('', false)).catch(() => {});
          }, { once: true });
        });
    };
    if (remoteVideo.readyState >= 2) tryPlay();
    else remoteVideo.addEventListener('loadedmetadata', tryPlay, { once: true });
  }

  function createPC(peerId) {
    if (pcs.has(peerId)) return pcs.get(peerId);
    const pc = new RTCPeerConnection({ iceServers });
    pcs.set(peerId, pc);
    iceQueues.set(peerId, []);

    pc.onicecandidate = (e) => {
      if (e.candidate) {
        send({
          type: 'ice',
          to: peerId,
          candidate: e.candidate.toJSON ? e.candidate.toJSON() : e.candidate,
        });
      }
    };

    pc.ontrack = (e) => {
      const stream = e.streams[0] || new MediaStream([e.track]);
      // Bir nechta track kelganda bir stream ga yig‘amiz
      if (remoteVideo && remoteVideo.srcObject) {
        const existing = remoteVideo.srcObject;
        stream.getTracks().forEach((t) => {
          if (!existing.getTracks().some((x) => x.id === t.id)) existing.addTrack(t);
        });
        attachRemoteStream(existing);
      } else {
        attachRemoteStream(stream);
      }
    };

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState;
      if (state === 'failed') {
        closePC(peerId);
        if (!isHost) {
          setPlaceholder('Aloqa uzildi — qayta ulanilmoqda…', true);
          send({ type: 'viewer-ready' });
        }
      } else if (state === 'closed') {
        pcs.delete(peerId);
      } else if (state === 'connected' && !isHost) {
        setPlaceholder('', false);
      }
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
    if (!isHost || !peerId) return;
    if (offering.has(peerId)) return;

    let pc = pcs.get(peerId);
    if (pc && ['connected', 'connecting'].includes(pc.connectionState)) return;
    if (pc && pc.signalingState === 'have-local-offer') return;
    if (pc && pc.signalingState !== 'stable') closePC(peerId);

    offering.add(peerId);
    try {
      pc = createPC(peerId);
      await addLocalTracks(pc);
      const offer = await pc.createOffer({
        offerToReceiveAudio: false,
        offerToReceiveVideo: false,
      });
      await pc.setLocalDescription(offer);
      send({
        type: 'offer',
        to: peerId,
        sdp: { type: pc.localDescription.type, sdp: pc.localDescription.sdp },
      });
    } catch (err) {
      console.error('hostOfferTo', err);
      closePC(peerId);
    } finally {
      offering.delete(peerId);
    }
  }

  async function handleOffer(from, sdp) {
    if (isHost || !from || !sdp) return;
    setPlaceholder('Efirga ulanilmoqda…', true);
    closePC(from);
    const pc = createPC(from);
    await pc.setRemoteDescription(sdp);
    await flushIce(from);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    send({
      type: 'answer',
      to: from,
      sdp: { type: pc.localDescription.type, sdp: pc.localDescription.sdp },
    });
  }

  async function handleAnswer(from, sdp) {
    const pc = pcs.get(from);
    if (!pc || !sdp) return;
    if (pc.signalingState === 'have-local-offer') {
      await pc.setRemoteDescription(sdp);
      await flushIce(from);
    }
  }

  async function handleIce(from, candidate) {
    if (!from || !candidate) return;
    const pc = pcs.get(from);
    if (!pc) return;
    if (!pc.remoteDescription) {
      const q = iceQueues.get(from) || [];
      q.push(candidate);
      iceQueues.set(from, q);
      return;
    }
    try {
      await pc.addIceCandidate(candidate);
    } catch (_) { /* ignore */ }
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
        setPlaceholder('Efirga ulanilmoqda…', true);
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
          if (!isHost && pcs.size === 0) {
            if (remoteVideo) remoteVideo.srcObject = null;
            setPlaceholder('O‘qituvchi efirdan chiqdi', true);
            if (unmuteBtn) unmuteBtn.hidden = true;
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

  if (unmuteBtn) {
    unmuteBtn.addEventListener('click', () => {
      if (!remoteVideo) return;
      remoteVideo.muted = false;
      remoteVideo.play().catch(() => {});
      unmuteBtn.hidden = true;
    });
  }

  if (chatForm && cfg.canChat) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      e.stopPropagation();
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
  });

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && isHost) attachLocalPreview();
    if (!document.hidden && !isHost && remoteVideo && remoteVideo.srcObject) {
      remoteVideo.play().catch(() => {});
    }
  });

  if (!isHost) setPlaceholder('Efirga ulanilmoqda…', true);
  connectWS();
})();
