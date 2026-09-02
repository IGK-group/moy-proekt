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
