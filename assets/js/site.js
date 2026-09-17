/* =========================================================================
   Regina Ruane — site behaviour
   Theme toggle, mobile nav, publication filters, scroll reveal, and the
   animated network in the home-page hero.
   ========================================================================= */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- theme ----------------------------------------------------------- */
  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  }
  function setTheme(next) {
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('rr-theme', next); } catch (e) { /* private mode */ }
    document.querySelectorAll('.theme-toggle').forEach(function (b) {
      b.setAttribute('aria-pressed', String(next === 'light'));
    });
    window.dispatchEvent(new CustomEvent('rr:themechange', { detail: { theme: next } }));
  }
  document.querySelectorAll('.theme-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  });

  /* ---- mobile nav ------------------------------------------------------ */
  var menuBtn = document.querySelector('.menu-btn');
  var sidebar = document.querySelector('.sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', function () {
      var open = sidebar.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.textContent = open ? 'Close' : 'Menu';
    });
    sidebar.querySelectorAll('.nav a').forEach(function (a) {
      a.addEventListener('click', function () {
        sidebar.classList.remove('is-open');
        menuBtn.setAttribute('aria-expanded', 'false');
        menuBtn.textContent = 'Menu';
      });
    });
  }

  /* ---- publication filters --------------------------------------------- */
  var filterBar = document.querySelector('.pub-filters');
  if (filterBar) {
    var pubs = Array.prototype.slice.call(document.querySelectorAll('.pub'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('[data-pub-group]'));
    var empty = document.querySelector('.pub-empty');

    filterBar.addEventListener('click', function (ev) {
      var btn = ev.target.closest('.filter-btn');
      if (!btn) return;
      var topic = btn.getAttribute('data-filter');

      filterBar.querySelectorAll('.filter-btn').forEach(function (b) {
        b.classList.toggle('is-active', b === btn);
        b.setAttribute('aria-pressed', String(b === btn));
      });

      var shown = 0;
      pubs.forEach(function (p) {
        var topics = (p.getAttribute('data-topics') || '').split(' ');
        var match = topic === 'all' || topics.indexOf(topic) !== -1;
        p.hidden = !match;
        if (match) shown++;
      });

      /* hide a section heading whose list is now empty */
      groups.forEach(function (g) {
        var any = g.querySelectorAll('.pub:not([hidden])').length > 0;
        g.hidden = !any;
      });

      if (empty) empty.classList.toggle('is-shown', shown === 0);
    });
  }

  /* ---- scroll reveal ---------------------------------------------------- */
  var revealables = document.querySelectorAll('.reveal');
  if (revealables.length) {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add('is-in');
            io.unobserve(e.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
      revealables.forEach(function (el, i) {
        el.style.transitionDelay = Math.min(i * 45, 260) + 'ms';
        io.observe(el);
      });
    }
  }

  /* ---- hero network ----------------------------------------------------- *
   * A small latent-space graph: nodes drift on a torus, edges appear between
   * nodes closer than a radius, so the graph rewires continuously. Sparse and
   * slow on purpose — it is a background, not a demo.
   * ---------------------------------------------------------------------- */
  var canvas = document.getElementById('net-canvas');
  if (canvas && canvas.getContext) {
    var ctx = canvas.getContext('2d');
    var nodes = [];
    var W = 0, H = 0, dpr = 1;
    var RADIUS = 132;          // connection distance in CSS px
    var raf = null;

    function palette() {
      var light = currentTheme() === 'light';
      return light
        ? { node: 'rgba(14,124,114,0.60)', edge: '14,124,114', halo: 'rgba(14,124,114,0.11)' }
        : { node: 'rgba(79,209,197,0.72)', edge: '79,209,197', halo: 'rgba(79,209,197,0.13)' };
    }
    var pal = palette();
    window.addEventListener('rr:themechange', function () { pal = palette(); });

    function resize() {
      var rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = rect.width; H = rect.height;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
    }

    function seed() {
      var density = Math.max(26, Math.min(62, Math.round((W * H) / 13500)));
      nodes = [];
      for (var i = 0; i < density; i++) {
        nodes.push({
          x: Math.random() * W,
          y: Math.random() * H,
          vx: (Math.random() - 0.5) * 0.19,
          vy: (Math.random() - 0.5) * 0.19,
          r: 1.1 + Math.random() * 1.9,
          /* a few high-degree nodes, as in a real degree distribution */
          hub: Math.random() < 0.13
        });
      }
    }

    function frame() {
      ctx.clearRect(0, 0, W, H);

      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        n.x += n.vx; n.y += n.vy;
        if (n.x < -20) n.x = W + 20; else if (n.x > W + 20) n.x = -20;
        if (n.y < -20) n.y = H + 20; else if (n.y > H + 20) n.y = -20;
      }

      /* edges */
      ctx.lineWidth = 0.7;
      for (var a = 0; a < nodes.length; a++) {
        var p = nodes[a];
        var reach = p.hub ? RADIUS * 1.5 : RADIUS;
        for (var b = a + 1; b < nodes.length; b++) {
          var q = nodes[b];
          var dx = p.x - q.x, dy = p.y - q.y;
          var d2 = dx * dx + dy * dy;
          var rr = Math.max(reach, q.hub ? RADIUS * 1.5 : RADIUS);
          if (d2 < rr * rr) {
            var alpha = (1 - Math.sqrt(d2) / rr) * 0.34;
            ctx.strokeStyle = 'rgba(' + pal.edge + ',' + alpha.toFixed(3) + ')';
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
          }
        }
      }

      /* nodes */
      for (var k = 0; k < nodes.length; k++) {
        var m = nodes[k];
        var rad = m.hub ? m.r * 1.85 : m.r;
        if (m.hub) {
          ctx.fillStyle = pal.halo;
          ctx.beginPath();
          ctx.arc(m.x, m.y, rad * 3.4, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.fillStyle = pal.node;
        ctx.beginPath();
        ctx.arc(m.x, m.y, rad, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(frame);
    }

    function start() {
      if (raf === null) raf = requestAnimationFrame(frame);
    }
    function stop() {
      if (raf !== null) { cancelAnimationFrame(raf); raf = null; }
    }

    resize();

    var resizeTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 180);
    });

    if (reduceMotion) {
      frame();          // one static frame
      stop();
    } else {
      start();
      document.addEventListener('visibilitychange', function () {
        if (document.hidden) stop(); else start();
      });
      /* stop drawing once the hero has scrolled away */
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { e.isIntersecting ? start() : stop(); });
        }, { threshold: 0 }).observe(canvas);
      }
    }
  }
})();
