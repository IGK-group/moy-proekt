/* ============================================================
   GlideHome prototype — общие интерактивы
   Поведение секций повторяет отраслевой стандарт витрины смарт-хоум:
   липкий хедер, hero-ротация, scroll-reveal, аккордеон, слайдер отзывов,
   sticky buy bar. Логика своя, ничего не срисовано с чужого кода.
   ============================================================ */
(function () {
  'use strict';

  /* ---- липкий хедер: класс condensed после прокрутки ---- */
  var hdr = document.getElementById('hdr');
  if (hdr) {
    var onScrollHdr = function () { hdr.classList.toggle('condensed', window.scrollY > 10); };
    addEventListener('scroll', onScrollHdr, { passive: true });
    onScrollHdr();
  }

  /* ---- мобильное меню ---- */
  var toggle = document.querySelector('.menu-toggle');
  var menu = document.querySelector('.menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.style.display === 'flex';
      menu.style.display = open ? '' : 'flex';
      menu.style.position = 'absolute';
      menu.style.flexDirection = 'column';
      menu.style.top = '100%';
      menu.style.left = '0';
      menu.style.right = '0';
      menu.style.background = 'var(--surface)';
      menu.style.padding = '16px 24px';
      menu.style.boxShadow = 'var(--shadow-md)';
    });
  }

  /* ---- HERO слайдер: авто-ротация + стрелки + точки с прогресс-заливкой ---- */
  var hero = document.querySelector('.hero .slides');
  if (hero) {
    var SLIDE_MS = 6000; // тайминг ротации: ~6 c на слайд (как у эталонных витрин)
    document.documentElement.style.setProperty('--slidems', SLIDE_MS + 'ms');
    var slides = [].slice.call(hero.querySelectorAll('.slide'));
    var dotsBox = document.getElementById('dots');
    var idx = 0, timer;

    slides.forEach(function (_, i) {
      var b = document.createElement('button');
      b.setAttribute('aria-label', 'Слайд ' + (i + 1));
      b.addEventListener('click', function () { go(i); reset(); });
      dotsBox.appendChild(b);
    });
    var dots = [].slice.call(dotsBox.children);

    var mq = window.matchMedia('(max-width:768px)');
    var isCarousel = function () { return mq.matches; };

    /* сдвиг трека на мобильном (px по реальной ширине слайда) */
    function setTrack(extraPx) {
      if (isCarousel()) {
        var w = hero.offsetWidth || 0;
        hero.style.transform = 'translateX(' + (-idx * w + (extraPx || 0)) + 'px)';
      } else {
        hero.style.transform = '';
      }
    }

    function go(n) {
      var prev = idx;
      idx = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('active', i === idx); });
      dots.forEach(function (d, i) {
        d.classList.remove('on');
        if (i === idx) { void d.offsetWidth; d.classList.add('on'); } // рестарт анимации заливки
      });
      if (isCarousel()) {
        var jump = Math.abs(idx - prev) > 1; // перескок через край — без анимации
        if (jump) hero.classList.add('no-anim');
        setTrack(0);
        if (jump) requestAnimationFrame(function () {
          requestAnimationFrame(function () { hero.classList.remove('no-anim'); });
        });
      }
    }
    function nextSlide() { go(idx + 1); }
    function reset() { clearInterval(timer); timer = setInterval(nextSlide, SLIDE_MS); }

    var nextBtn = document.getElementById('next');
    var prevBtn = document.getElementById('prev');
    if (nextBtn) nextBtn.addEventListener('click', function () { nextSlide(); reset(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { go(idx - 1); reset(); });

    hero.addEventListener('mouseenter', function () { clearInterval(timer); });
    hero.addEventListener('mouseleave', reset);
    addEventListener('resize', function () { hero.classList.add('no-anim'); setTrack(0);
      requestAnimationFrame(function () { hero.classList.remove('no-anim'); }); });

    /* тач-драг: трек цепляется за палец, на отпускании — доводчик */
    var swArea = hero.closest('.hero') || hero;
    var sx = 0, sy = 0, cx = 0, cy = 0, tracking = false, dragging = false, pLock = false;

    function dragStart(x, y) {
      sx = cx = x; sy = cy = y; tracking = true; dragging = false;
      clearInterval(timer);
    }
    function dragMove(x, y) {
      if (!tracking) return;
      cx = x; cy = y;
      var dx = cx - sx, dy = cy - sy;
      if (!dragging && Math.abs(dx) > 6 && Math.abs(dx) > Math.abs(dy)) {
        dragging = true;
        hero.classList.add('no-anim');
      }
      if (dragging && isCarousel()) {
        // сопротивление на краях
        if ((idx === 0 && dx > 0) || (idx === slides.length - 1 && dx < 0)) dx *= 0.35;
        setTrack(dx);
      }
    }
    function dragEnd() {
      if (!tracking) return;
      tracking = false;
      var dx = cx - sx, dy = cy - sy;
      hero.classList.remove('no-anim');
      if (isCarousel()) {
        if (dragging) {
          dragging = false;
          var w = hero.offsetWidth || 1;
          var far = Math.abs(dx) > w * 0.16 && Math.abs(dx) > Math.abs(dy);
          if (far && dx < 0 && idx < slides.length - 1) go(idx + 1);
          else if (far && dx > 0 && idx > 0) go(idx - 1);
          else setTrack(0); // доводчик назад
        }
      } else if (Math.abs(dx) > 38 && Math.abs(dx) > Math.abs(dy)) {
        go(dx < 0 ? idx + 1 : idx - 1);
      }
      reset();
    }

    if (window.PointerEvent) {
      swArea.addEventListener('pointerdown', function (e) {
        if (e.pointerType === 'mouse') return;
        pLock = true; dragStart(e.clientX, e.clientY);
      });
      swArea.addEventListener('pointermove', function (e) { if (pLock) dragMove(e.clientX, e.clientY); }, { passive: true });
      swArea.addEventListener('pointerup', function () { if (pLock) { pLock = false; dragEnd(); } });
      swArea.addEventListener('pointercancel', function () { if (pLock) { pLock = false; dragEnd(); } });
    }
    swArea.addEventListener('touchstart', function (e) {
      if (pLock) return;
      var t = e.changedTouches[0]; dragStart(t.clientX, t.clientY);
    }, { passive: true });
    swArea.addEventListener('touchmove', function (e) {
      if (pLock) return;
      var t = e.changedTouches[0]; dragMove(t.clientX, t.clientY);
    }, { passive: true });
    swArea.addEventListener('touchend', function (e) {
      if (pLock) return;
      if (e.changedTouches[0]) { cx = e.changedTouches[0].clientX; cy = e.changedTouches[0].clientY; }
      dragEnd();
    }, { passive: true });
    swArea.addEventListener('touchcancel', function () { if (!pLock) dragEnd(); }, { passive: true });

    go(0);
    setTrack(0);
    reset();
  }

  /* ---- scroll-reveal ---- */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.18 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  /* ---- FAQ: аккордеон-эксклюзив (открыт только один) ---- */
  var qas = [].slice.call(document.querySelectorAll('.qa'));
  qas.forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (d.open) qas.forEach(function (o) { if (o !== d) o.open = false; });
    });
  });

  /* ---- FAQ: "показать все / свернуть" ---- */
  var faqToggle = document.querySelector('[data-faq-toggle]');
  if (faqToggle) {
    var hidden = [].slice.call(document.querySelectorAll('.qa[data-extra]'));
    hidden.forEach(function (q) { q.hidden = true; });
    var shown = false;
    faqToggle.addEventListener('click', function () {
      shown = !shown;
      hidden.forEach(function (q) { q.hidden = !shown; });
      faqToggle.textContent = shown ? 'Свернуть' : 'Показать все вопросы';
    });
  }

  /* ---- слайдер отзывов ---- */
  var revTrack = document.querySelector('.rev-track');
  if (revTrack) {
    var revs = revTrack.children.length;
    var r = 0;
    var move = function (n) { r = (n + revs) % revs; revTrack.style.transform = 'translateX(-' + (r * 100) + '%)'; };
    var rp = document.querySelector('[data-rev-prev]');
    var rn = document.querySelector('[data-rev-next]');
    if (rp) rp.addEventListener('click', function () { move(r - 1); });
    if (rn) rn.addEventListener('click', function () { move(r + 1); });
    setInterval(function () { move(r + 1); }, 7000);
  }

  /* ---- sticky mobile buy bar: показываем после hero ---- */
  var buybar = document.getElementById('buybar');
  if (buybar) {
    var anchor = document.querySelector('.hero, .hero-static, .pdp');
    addEventListener('scroll', function () {
      if (!anchor) return;
      var past = window.scrollY > anchor.offsetTop + anchor.offsetHeight - 120;
      buybar.classList.toggle('show', past);
    }, { passive: true });
  }

  /* ---- PDP: галерея + свотчи ---- */
  var gMain = document.querySelector('.gallery .main img');
  document.querySelectorAll('.gallery .thumbs button').forEach(function (t) {
    t.addEventListener('click', function () {
      document.querySelectorAll('.gallery .thumbs button').forEach(function (b) { b.classList.remove('on'); });
      t.classList.add('on');
      if (gMain && t.dataset.src) gMain.src = t.dataset.src;
    });
  });
  document.querySelectorAll('.swatches button').forEach(function (s) {
    s.addEventListener('click', function () {
      document.querySelectorAll('.swatches button').forEach(function (b) { b.classList.remove('on'); });
      s.classList.add('on');
    });
  });
})();
