/* GlideHome hero — кроссфейд на десктопе + тач-карусель «за пальцем» на мобильном.
   Порт из store-redesign-prototype/app.js. Инициализация по [data-glide-hero]. */
(function () {
  'use strict';

  function initHero(root) {
    var track = root.querySelector('[data-glide-track]');
    var dotsBox = root.querySelector('[data-glide-dots]');
    if (!track || !dotsBox) return;
    var slides = [].slice.call(track.querySelectorAll('[data-glide-slide]'));
    if (slides.length < 2) return;

    var SLIDE_MS = parseInt(root.getAttribute('data-autoplay-ms') || '6000', 10);
    var idx = 0, timer;
    var mq = window.matchMedia('(max-width: 768px)');
    var isCarousel = function () { return mq.matches; };

    slides.forEach(function (_, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Slide ' + (i + 1));
      b.addEventListener('click', function () { go(i); reset(); });
      dotsBox.appendChild(b);
    });
    var dots = [].slice.call(dotsBox.children);

    function setTrack(extraPx) {
      if (isCarousel()) {
        var w = track.offsetWidth || 0;
        track.style.transform = 'translateX(' + (-idx * w + (extraPx || 0)) + 'px)';
      } else {
        track.style.transform = '';
      }
    }

    function go(n) {
      var prev = idx;
      idx = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('is-active', i === idx); });
      dots.forEach(function (d, i) { d.classList.toggle('is-on', i === idx); });
      if (isCarousel()) {
        var jump = Math.abs(idx - prev) > 1;
        if (jump) track.classList.add('is-noanim');
        setTrack(0);
        if (jump) requestAnimationFrame(function () {
          requestAnimationFrame(function () { track.classList.remove('is-noanim'); });
        });
      }
    }
    function nextSlide() { go(idx + 1); }
    function reset() { clearInterval(timer); timer = setInterval(nextSlide, SLIDE_MS); }

    var nextBtn = root.querySelector('[data-glide-next]');
    var prevBtn = root.querySelector('[data-glide-prev]');
    if (nextBtn) nextBtn.addEventListener('click', function () { nextSlide(); reset(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { go(idx - 1); reset(); });

    root.addEventListener('mouseenter', function () { clearInterval(timer); });
    root.addEventListener('mouseleave', reset);
    addEventListener('resize', function () {
      track.classList.add('is-noanim'); setTrack(0);
      requestAnimationFrame(function () { track.classList.remove('is-noanim'); });
    });

    /* тач-драг */
    var sx = 0, sy = 0, cx = 0, cy = 0, tracking = false, dragging = false, pLock = false;
    function dragStart(x, y) { sx = cx = x; sy = cy = y; tracking = true; dragging = false; clearInterval(timer); }
    function dragMove(x, y) {
      if (!tracking) return;
      cx = x; cy = y;
      var dx = cx - sx, dy = cy - sy;
      if (!dragging && Math.abs(dx) > 6 && Math.abs(dx) > Math.abs(dy)) {
        dragging = true; track.classList.add('is-noanim');
      }
      if (dragging && isCarousel()) {
        if ((idx === 0 && dx > 0) || (idx === slides.length - 1 && dx < 0)) dx *= 0.35;
        setTrack(dx);
      }
    }
    function dragEnd() {
      if (!tracking) return;
      tracking = false;
      var dx = cx - sx, dy = cy - sy;
      track.classList.remove('is-noanim');
      if (isCarousel()) {
        if (dragging) {
          dragging = false;
          var w = track.offsetWidth || 1;
          var far = Math.abs(dx) > w * 0.16 && Math.abs(dx) > Math.abs(dy);
          if (far && dx < 0 && idx < slides.length - 1) go(idx + 1);
          else if (far && dx > 0 && idx > 0) go(idx - 1);
          else setTrack(0);
        }
      } else if (Math.abs(dx) > 38 && Math.abs(dx) > Math.abs(dy)) {
        go(dx < 0 ? idx + 1 : idx - 1);
      }
      reset();
    }
    if (window.PointerEvent) {
      root.addEventListener('pointerdown', function (e) {
        if (e.pointerType === 'mouse') return;
        pLock = true; dragStart(e.clientX, e.clientY);
      });
      root.addEventListener('pointermove', function (e) { if (pLock) dragMove(e.clientX, e.clientY); }, { passive: true });
      root.addEventListener('pointerup', function () { if (pLock) { pLock = false; dragEnd(); } });
      root.addEventListener('pointercancel', function () { if (pLock) { pLock = false; dragEnd(); } });
    }
    root.addEventListener('touchstart', function (e) {
      if (pLock) return;
      var t = e.changedTouches[0]; dragStart(t.clientX, t.clientY);
    }, { passive: true });
    root.addEventListener('touchmove', function (e) {
      if (pLock) return;
      var t = e.changedTouches[0]; dragMove(t.clientX, t.clientY);
      if (dragging && e.cancelable) e.preventDefault();
    }, { passive: false });
    root.addEventListener('touchend', function (e) {
      if (pLock) return;
      if (e.changedTouches[0]) { cx = e.changedTouches[0].clientX; cy = e.changedTouches[0].clientY; }
      dragEnd();
    }, { passive: true });
    root.addEventListener('touchcancel', function () { if (!pLock) dragEnd(); }, { passive: true });

    go(0);
    setTrack(0);
    reset();
  }

  function boot() {
    document.querySelectorAll('[data-glide-hero]').forEach(initHero);
  }
  if (document.readyState !== 'loading') boot();
  else document.addEventListener('DOMContentLoaded', boot);
  // повторная инициализация при добавлении секции в Theme Editor
  document.addEventListener('shopify:section:load', function (e) {
    e.target.querySelectorAll('[data-glide-hero]').forEach(initHero);
  });
})();
