/* XYZ motion layer: reveal, counters, nav scroll, page enter */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function reveal() {
    const nodes = document.querySelectorAll('.reveal');
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

  function pageEnter() {
    if (reduce) return;
    document.documentElement.classList.add('page-enter');
  }

  function tiltCards() {
    if (reduce || window.matchMedia('(pointer: coarse)').matches) return;
    document.querySelectorAll('.person-card, .subject-tile').forEach((card) => {
      card.addEventListener('pointermove', (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `perspective(700px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-4px)`;
      });
      card.addEventListener('pointerleave', () => {
        card.style.transform = '';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    pageEnter();
    reveal();
    animateCounters();
    navScroll();
    tiltCards();
  });
})();
