/* Abschlusswerkstatt: Menüzeile mit Untermenüs, mobiles Menü und Bereichsleiste. */
(function () {
  var doc = document.documentElement;
  doc.classList.add('js');

  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };
  var gn = document.getElementById('gn');

  if (gn) {
    var curtain = document.getElementById('gn-curtain');
    var fine = window.matchMedia('(hover: hover) and (pointer: fine)');
    var current = null;
    var openTimer = 0;
    var closeTimer = 0;

    var setOpen = function (item) {
      if (current === item) return;
      if (current) {
        current.classList.remove('is-open');
        current.querySelector('.gn-open').setAttribute('aria-expanded', 'false');
      }
      current = item || null;
      if (current) {
        current.classList.add('is-open');
        current.querySelector('.gn-open').setAttribute('aria-expanded', 'true');
      }
      gn.classList.toggle('has-open', !!current);
      if (curtain) curtain.classList.toggle('is-on', !!current);
    };

    each(gn.querySelectorAll('.gn-has'), function (item) {
      item.addEventListener('mouseenter', function () {
        if (!fine.matches) return;
        clearTimeout(closeTimer);
        clearTimeout(openTimer);
        openTimer = setTimeout(function () { setOpen(item); }, current ? 0 : 140);
      });
      item.addEventListener('mouseleave', function () {
        clearTimeout(openTimer);
        closeTimer = setTimeout(function () { setOpen(null); }, 160);
      });
      item.querySelector('.gn-open').addEventListener('click', function () {
        setOpen(current === item ? null : item);
      });
    });

    each(gn.querySelectorAll('.gn-item:not(.gn-has), .gn-brand, .gn-mail'), function (el) {
      el.addEventListener('mouseenter', function () {
        clearTimeout(openTimer);
        if (!current) return;
        clearTimeout(closeTimer);
        closeTimer = setTimeout(function () { setOpen(null); }, 60);
      });
    });

    gn.addEventListener('focusout', function (e) {
      if (current && !current.contains(e.relatedTarget)) setOpen(null);
    });
    if (curtain) curtain.addEventListener('click', function () { setOpen(null); });

    var burger = gn.querySelector('.gn-burger');
    var panel = document.getElementById('gn-mobile');
    var menuOpen = function () { return !!burger && burger.getAttribute('aria-expanded') === 'true'; };
    var toggleMenu = function (open) {
      if (!burger || !panel) return;
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Menü schließen' : 'Menü öffnen');
      panel.hidden = !open;
      doc.classList.toggle('menu-open', open);
    };
    if (burger) burger.addEventListener('click', function () { toggleMenu(!menuOpen()); });

    each(document.querySelectorAll('.gm-toggle'), function (btn) {
      btn.addEventListener('click', function () {
        var open = btn.getAttribute('aria-expanded') !== 'true';
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        var sub = document.getElementById(btn.getAttribute('aria-controls'));
        if (sub) sub.hidden = !open;
      });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      if (current) {
        var btn = current.querySelector('.gn-open');
        setOpen(null);
        btn.focus();
      }
      if (menuOpen()) {
        toggleMenu(false);
        burger.focus();
      }
    });

    var wide = window.matchMedia('(min-width: 834px)');
    var onWidth = function () { if (wide.matches) toggleMenu(false); else setOpen(null); };
    if (wide.addEventListener) wide.addEventListener('change', onWidth);
    else if (wide.addListener) wide.addListener(onWidth);
  }

  Array.prototype.forEach.call(document.querySelectorAll('.copy[data-copy]'), function (btn) {
    var label = btn.textContent;
    var timer;
    btn.addEventListener('click', function () {
      var src = document.getElementById(btn.getAttribute('data-copy'));
      if (!src) return;
      var text = src.textContent;
      var done = function (ok) {
        btn.textContent = ok ? 'Kopiert' : 'Bitte markieren';
        clearTimeout(timer);
        timer = setTimeout(function () { btn.textContent = label; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        var range = document.createRange();
        range.selectNodeContents(src);
        var sel = window.getSelection();
        sel.removeAllRanges(); sel.addRange(range);
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (e) {}
        done(ok);
      }
    });
  });

  var ln = document.querySelector('.ln');
  if (ln) {
    var toggle = ln.querySelector('.ln-toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var open = !ln.classList.contains('is-open');
        ln.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }
  }
})();
