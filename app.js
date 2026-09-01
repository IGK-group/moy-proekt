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

    function go(n) {
      idx = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('active', i === idx); });
      dots.forEach(function (d, i) {
        d.classList.remove('on');
        if (i === idx) { void d.offsetWidth; d.classList.add('on'); } // рестарт анимации заливки
      });
    }
    function nextSlide() { go(idx + 1); }
    function reset() { clearInterval(timer); timer = setInterval(nextSlide, SLIDE_MS); }

    var nextBtn = document.getElementById('next');
    var prevBtn = document.getElementById('prev');
    if (nextBtn) nextBtn.addEventListener('click', function () { nextSlide(); reset(); });
    if (prevBtn) prevBtn.addEventListener('click', function () { go(idx - 1); reset(); });

    hero.addEventListener('mouseenter', function () { clearInterval(timer); });
    hero.addEventListener('mouseleave', reset);

    go(0);
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
