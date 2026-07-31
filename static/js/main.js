/* XYZ motion: reveal, counters, nav scroll, hash, hero lock, page loader */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function reveal() {
    const nodes = document.querySelectorAll('.reveal:not(.is-visible)');
    if (!nodes.length) return;
    if (reduce) {
      nodes.forEach((el) => el.classList.add('is-visible'));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    nodes.forEach((el) => io.observe(el));
  }

  function animateCounters() {
    const counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;
    const run = (el) => {
      const target = Number(el.getAttribute('data-count') || 0);
      if (reduce) {
        el.textContent = String(target);
        return;
      }
      const duration = 900;
      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = String(Math.round(target * eased));
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            run(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    counters.forEach((el) => io.observe(el));
  }

  function navScroll() {
    const nav = document.querySelector('.xyz-nav');
    if (!nav) return;
    const onScroll = () => {
      nav.classList.toggle('is-scrolled', window.scrollY > 12);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  function scrollToHash() {
    if (!window.location.hash) return;
    const el = document.getElementById(window.location.hash.slice(1));
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
  }

  function lockHeroVideo() {
    const v = document.getElementById('hero-bg-video');
    if (!v) return;
    v.muted = true;
    v.defaultMuted = true;
    v.controls = false;
    v.removeAttribute('controls');
    const play = () => v.play().catch(() => {});
    ['pause', 'seeking', 'seeked', 'ratechange', 'volumechange'].forEach((ev) => {
      v.addEventListener(ev, () => {
        v.muted = true;
        if (ev === 'pause' || ev === 'seeking' || ev === 'seeked') play();
      });
    });
    document.addEventListener('keydown', (e) => {
      const t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
      if ([' ', 'ArrowLeft', 'ArrowRight', 'j', 'l', 'J', 'L', 'k', 'K', 'm', 'M'].includes(e.key)) {
        e.preventDefault();
      }
    });
    play();
  }

  function pageLoader() {
    const el = document.getElementById('xyz-loader');
    if (!el) return;

    let hideTimer = null;
    const show = () => {
      el.hidden = false;
      el.setAttribute('aria-hidden', 'false');
      requestAnimationFrame(() => el.classList.add('is-on'));
      clearTimeout(hideTimer);
      // Agar navigatsiya to‘xtasa — 12s dan keyin yopiladi
      hideTimer = setTimeout(hide, 12000);
    };
    const hide = () => {
      clearTimeout(hideTimer);
      el.classList.remove('is-on');
      el.setAttribute('aria-hidden', 'true');
      setTimeout(() => {
        if (!el.classList.contains('is-on')) el.hidden = true;
      }, 280);
    };

    const sameOriginNav = (url) => {
      try {
        const u = new URL(url, window.location.href);
        if (u.origin !== window.location.origin) return false;
        if (u.pathname === window.location.pathname && u.search === window.location.search && u.hash) {
          return false; // faqat hash
        }
        return true;
      } catch (_) {
        return false;
      }
    };

    document.addEventListener('click', (e) => {
      if (e.defaultPrevented) return;
      if (e.button !== 0) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = e.target.closest('a[href]');
      if (!a) return;
      if (a.target === '_blank' || a.hasAttribute('download')) return;
      if (a.getAttribute('href')?.startsWith('mailto:') || a.getAttribute('href')?.startsWith('tel:')) return;
      if (a.dataset.noLoader === '1') return;
      if (!sameOriginNav(a.href)) return;
      show();
    });

    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (form.dataset.noLoader === '1') return;
      if (form.id === 'live-chat-form') return;
      if (e.defaultPrevented) return;
      if (form.target === '_blank') return;
      const method = (form.method || 'get').toLowerCase();
      if (method === 'get' || method === 'post') show();
    });

    window.addEventListener('pageshow', hide);
    window.addEventListener('pagehide', () => {});
    document.addEventListener('DOMContentLoaded', hide);
    // bfcache / tez orqaga
    window.addEventListener('popstate', () => setTimeout(hide, 50));
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.documentElement.classList.add('page-enter');
    reveal();
    animateCounters();
    navScroll();
    scrollToHash();
    lockHeroVideo();
  });
  pageLoader();
  window.addEventListener('hashchange', scrollToHash);
})();
