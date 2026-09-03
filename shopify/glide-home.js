/* GlideHome hero.
   Десктоп: кроссфейд слайдов (opacity) + автопрокрутка.
   Мобильный (<=768px): нативный CSS scroll-snap — свайп работает без JS.
   JS только доводит автопрокрутку и точки-индикатор. */
(function () {
  'use strict';

  function initHero(root) {
    var track = root.querySelector('[data-glide-track]');
    var dotsBox = root.querySelector('[data-glide-dots]');
    if (!track || !dotsBox) return;
    var slides = [].slice.call(track.querySelectorAll('[data-glide-slide]'));
    if (slides.length < 2) return;

    var SLIDE_MS = parseInt(root.getAttribute('data-autoplay-ms') || '6000', 10);
    var idx = 0, timer = null;
    var mq = window.matchMedia('(max-width: 768px)');
    var isMobile = function () { return mq.matches; };

    // точки
    slides.forEach(function (_, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Slide ' + (i + 1));
      b.addEventListener('click', function () { go(i, true); restart(); });
      dotsBox.appendChild(b);
    });
    var dots = [].slice.call(dotsBox.children);

    function paint() {
      slides.forEach(function (s, i) { s.classList.toggle('is-active', i === idx); });
      dots.forEach(function (d, i) { d.classList.toggle('is-on', i === idx); });
    }

    function go(n, smooth) {
      idx = (n + slides.length) % slides.length;
      if (isMobile()) {
        track.scrollTo({ left: idx * track.clientWidth, behavior: smooth ? 'smooth' : 'auto' });
      }
      paint();
    }
    function next() { go(idx + 1, true); }
    function restart() {
      if (timer) clearInterval(timer);
      timer = setInterval(next, SLIDE_MS);
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }

    // мобильный: следим за нативным скроллом, обновляем idx/точки
    var scrollRaf = null;
    track.addEventListener('scroll', function () {
      if (!isMobile()) return;
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(function () {
        scrollRaf = null;
        var w = track.clientWidth || 1;
        var n = Math.round(track.scrollLeft / w);
        if (n !== idx && n >= 0 && n < slides.length) { idx = n; paint(); }
      });
    }, { passive: true });

    // пауза автопрокрутки, пока трогают/скроллят
    var pauseT = null;
    function bump() { stop(); if (pauseT) clearTimeout(pauseT); pauseT = setTimeout(restart, 2500); }
    track.addEventListener('pointerdown', bump);
    track.addEventListener('touchstart', bump, { passive: true });
    track.addEventListener('wheel', bump, { passive: true });

    var prev = root.querySelector('[data-glide-prev]');
    var nextBtn = root.querySelector('[data-glide-next]');
    if (prev) prev.addEventListener('click', function () { go(idx - 1, true); restart(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { go(idx + 1, true); restart(); });

    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', restart);

    // при смене вида (десктоп<->мобайл) выставить позицию
    var onMode = function () { go(idx, false); };
    if (mq.addEventListener) mq.addEventListener('change', onMode);
    addEventListener('resize', function () { if (isMobile()) track.scrollLeft = idx * track.clientWidth; });

    go(0, false);
    restart();
  }

  function boot() { document.querySelectorAll('[data-glide-hero]').forEach(initHero); }
  if (document.readyState !== 'loading') boot();
  else document.addEventListener('DOMContentLoaded', boot);
  document.addEventListener('shopify:section:load', function (e) {
    e.target.querySelectorAll('[data-glide-hero]').forEach(initHero);
  });
})();

/* GlideHome content sections: scroll-reveal + FAQ view-all toggle. */
(function () {
  'use strict';
  function reveal() {
    var els = document.querySelectorAll('.glide-reveal:not(.is-in)');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (e) { e.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
    els.forEach(function (e) { io.observe(e); });
    setTimeout(function () {
      document.querySelectorAll('.glide-reveal:not(.is-in)').forEach(function (e) { e.classList.add('is-in'); });
    }, 2500);
  }
  function faq() {
    document.querySelectorAll('[data-glide-faq-toggle]').forEach(function (btn) {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', function () {
        var sec = btn.closest('[data-glide-faq]');
        var open = sec.classList.toggle('is-open');
        btn.textContent = open ? btn.getAttribute('data-less') : btn.getAttribute('data-more');
        if (!open) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }
  function boot() { reveal(); faq(); }
  if (document.readyState !== 'loading') boot();
  else document.addEventListener('DOMContentLoaded', boot);
  document.addEventListener('shopify:section:load', boot);
})();

/* GlideHome scroll-memory: вернуться ровно туда, откуда ушёл (любая страница). */
(function () {
  'use strict';
  var ss;
  try { ss = window.sessionStorage; } catch (e) { return; }
  if (!ss) return;
  var KEY = 'glide:sy:' + location.pathname + location.search;

  function save() {
    try { ss.setItem(KEY, String(window.scrollY || window.pageYOffset || 0)); } catch (e) {}
  }
  // сохраняем при любом уходе со страницы
  window.addEventListener('pagehide', save);
  window.addEventListener('beforeunload', save);
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    try {
      var u = new URL(a.href, location.href);
      if (u.origin === location.origin && (u.pathname !== location.pathname || u.search !== location.search)) save();
    } catch (err) {}
  }, true);

  // восстанавливаем при заходе, если для этого адреса есть сохранённая позиция
  var saved = ss.getItem(KEY);
  if (saved === null) return;
  var y = parseInt(saved, 10) || 0;
  if (y <= 0) return;
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  var tries = 0;
  function restore() {
    window.scrollTo(0, y);
    if (++tries < 12 && Math.abs((window.scrollY || 0) - y) > 2) setTimeout(restore, 80);
  }
  restore();
  requestAnimationFrame(restore);
  window.addEventListener('load', function () { setTimeout(restore, 30); });
})();
