/* «Мягкий Свет» — интерактив сайта. Настройки берутся из config.js */
(function () {
  "use strict";

  var C = window.SITE_CONFIG || {};
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var icon = function (name) { return '<svg class="icon" aria-hidden="true"><use href="#i-' + name + '"/></svg>'; };
  var rub = function (n) { return Number(n).toLocaleString("ru-RU") + " ₽"; };
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };

  /* ---------- 1. Подстановка данных из config.js ---------- */
  function applyConfig() {
    $$("[data-site]").forEach(function (el) {
      var key = el.getAttribute("data-site");
      if (C[key] !== undefined && C[key] !== null) el.textContent = C[key];
    });
    $$("[data-site-href='tel']").forEach(function (el) { if (C.phoneHref) el.setAttribute("href", "tel:" + C.phoneHref); });
    $$("[data-site-href='mailto']").forEach(function (el) { if (C.email) el.setAttribute("href", "mailto:" + C.email); });
    $$("[data-site-block]").forEach(function (el) {
      var key = el.getAttribute("data-site-block");
      var val = C[key];
      var empty = !val || (Array.isArray(val) && !val.length);
      el.hidden = empty;
    });
    $$("[data-site-list]").forEach(function (el) {
      var list = C[el.getAttribute("data-site-list")] || [];
      el.innerHTML = list.map(function (item) {
        return '<a class="chip" href="' + esc(item.url) + '" target="_blank" rel="noopener">' + icon("chat") + esc(item.label) + "</a>";
      }).join("");
    });
    $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
    if (C.demoPrices) document.documentElement.classList.add("is-demo-prices");
  }

  /* ---------- 2. Шапка, мега-меню, мобильное меню ---------- */
  function initHeader() {
    var header = $(".site-header");
    var backdrop = $(".nav-backdrop");
    if (!header) return;

    var setH = function () { document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px"); };
    setH();
    window.addEventListener("resize", setH);

    var items = $$(".nav__item.has-mega");
    var closeTimer = null;
    var closeAll = function () {
      items.forEach(function (it) { it.classList.remove("is-open"); var b = $(".nav__link", it); if (b) b.setAttribute("aria-expanded", "false"); });
      if (backdrop) backdrop.classList.remove("is-visible");
    };
    var open = function (it) {
      clearTimeout(closeTimer);
      items.forEach(function (o) { if (o !== it) { o.classList.remove("is-open"); var ob = $(".nav__link", o); if (ob) ob.setAttribute("aria-expanded", "false"); } });
      it.classList.add("is-open");
      $(".nav__link", it).setAttribute("aria-expanded", "true");
      if (backdrop) backdrop.classList.add("is-visible");
    };
    var canHover = window.matchMedia("(hover: hover)").matches;
    items.forEach(function (it) {
      var btn = $(".nav__link", it);
      btn.addEventListener("click", function (e) {
        // Мышью на десктопе меню уже открыто наведением — клик его не закрывает
        if (canHover && e.detail > 0) { open(it); return; }
        it.classList.contains("is-open") ? closeAll() : open(it);
      });
      if (canHover) {
        it.addEventListener("mouseenter", function () { open(it); });
        it.addEventListener("mouseleave", function () { closeTimer = setTimeout(closeAll, 160); });
      }
    });
    if (backdrop) backdrop.addEventListener("click", closeAll);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { closeAll(); closeMobile(); } });
    document.addEventListener("click", function (e) { if (!e.target.closest(".nav")) closeAll(); });

    // Мобильное меню
    var burger = $(".topbar__burger");
    var menu = $("#mobile-menu");
    function closeMobile() {
      if (!menu || !burger) return;
      menu.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
      burger.innerHTML = icon("menu");
      document.body.style.overflow = "";
    }
    if (burger && menu) {
      burger.addEventListener("click", function () {
        var isOpen = menu.classList.toggle("is-open");
        burger.setAttribute("aria-expanded", String(isOpen));
        burger.innerHTML = icon(isOpen ? "close" : "menu");
        document.body.style.overflow = isOpen ? "hidden" : "";
      });
      $$(".m-nav__link[aria-controls]", menu).forEach(function (btn) {
        btn.addEventListener("click", function () {
          var sub = document.getElementById(btn.getAttribute("aria-controls"));
          var exp = btn.getAttribute("aria-expanded") === "true";
          btn.setAttribute("aria-expanded", String(!exp));
          sub.hidden = exp;
        });
      });
      $$("a", menu).forEach(function (a) { a.addEventListener("click", closeMobile); });
      window.addEventListener("resize", function () { if (window.innerWidth > 1024) closeMobile(); });
    }
    window.__closeMobileMenu = closeMobile;
  }

  /* ---------- 3. Таблицы цен ---------- */
  var TAB_GROUPS = [
    { id: "cat", label: "Кошки", icon: "cat", species: ["cat"] },
    { id: "dog", label: "Собаки", icon: "dog", species: ["dog"] },
    { id: "other", label: "Другие животные", icon: "paw", species: ["small", "bird", "exotic"] }
  ];

  function minPrice(serviceId) {
    var s = C.services && C.services[serviceId];
    if (!s) return null;
    return Math.min.apply(null, Object.keys(s.prices).map(function (k) { return s.prices[k]; }));
  }

  function priceRows(group, cols) {
    var rows = [];
    group.species.forEach(function (sid) {
      var sp = C.species[sid];
      sp.weights.forEach(function (wid) {
        var w = C.weights.filter(function (x) { return x.id === wid; })[0];
        var name = group.species.length === 1 ? w.label : sp.label + (sp.weights.length > 1 ? ", " + w.label : "");
        rows.push("<tr><th scope=\"row\">" + esc(name) + "</th>" + cols.map(function (c) { return "<td>" + rub(C.services[c].prices[wid]) + "</td>"; }).join("") + "</tr>");
      });
    });
    return rows.join("");
  }

  function renderPriceTables() {
    $$("[data-price-table]").forEach(function (box, n) {
      var mode = box.getAttribute("data-price-table"); // all | euth | cremation
      var cols = mode === "euth" ? ["euth"] : mode === "cremation" ? ["common", "individual"] : ["euth", "common", "individual"];
      var tabsId = "pt" + n;
      var html = '<div class="tabs" role="tablist" aria-label="Вид питомца">';
      TAB_GROUPS.forEach(function (g, i) {
        html += '<button class="tab" role="tab" type="button" id="' + tabsId + "-t" + i + '" aria-controls="' + tabsId + "-p" + i + '" aria-selected="' + (i === 0) + '" tabindex="' + (i === 0 ? 0 : -1) + '">' + icon(g.icon) + esc(g.label) + "</button>";
      });
      html += "</div>";
      TAB_GROUPS.forEach(function (g, i) {
        html += '<div class="table-wrap" role="tabpanel" id="' + tabsId + "-p" + i + '" aria-labelledby="' + tabsId + "-t" + i + '"' + (i === 0 ? "" : " hidden") + ">";
        html += '<table class="price-table"><thead><tr><th scope="col">' + (g.species.length > 1 ? "Питомец" : "Вес питомца") + "</th>";
        cols.forEach(function (c) { html += '<th scope="col">' + esc(C.services[c].label) + "<br><small>" + esc(C.services[c].note) + "</small></th>"; });
        html += "</tr></thead><tbody>" + priceRows(g, cols);
        if (mode !== "euth") {
          html += '<tr class="row-sep"><th scope="row">' + esc(C.extras.pickup.label) + '</th><td colspan="' + cols.length + '">' + rub(C.extras.pickup.price) + "</td></tr>";
        }
        html += '<tr><th scope="row">Выезд за город</th><td class="muted" colspan="' + cols.length + '">по зоне: от ' + rub(zoneMin()) + ' · <a href="zona.html">зоны выезда</a></td></tr>';
        html += "</tbody></table></div>";
      });
      box.innerHTML = html;
      initTabs(box);
    });

    $$("[data-price-from]").forEach(function (el) {
      var id = el.getAttribute("data-price-from");
      var v = C.services[id] ? minPrice(id) : C.extras[id] ? C.extras[id].price : null;
      if (v !== null) el.textContent = rub(v);
    });
  }

  function zoneMin() {
    var vals = (C.zones || []).map(function (z) { return z.price; }).filter(function (p) { return typeof p === "number" && p > 0; });
    return vals.length ? Math.min.apply(null, vals) : 0;
  }

  function initTabs(root) {
    var tabs = $$("[role=tab]", root);
    var select = function (t) {
      tabs.forEach(function (x) {
        var on = x === t;
        x.setAttribute("aria-selected", String(on));
        x.tabIndex = on ? 0 : -1;
        document.getElementById(x.getAttribute("aria-controls")).hidden = !on;
      });
    };
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        var next = tabs[(i + d + tabs.length) % tabs.length];
        next.focus(); select(next);
      });
    });
  }

  /* ---------- 4. Зоны выезда ---------- */
  function renderZones() {
    $$("[data-zone-list]").forEach(function (el) {
      el.innerHTML = (C.zones || []).map(function (z) {
        var p = z.price === null ? "по договорённости" : z.price === 0 ? "выезд без доплаты" : "доплата " + rub(z.price);
        return '<div class="zone__row"><span class="zone__row-name"><span class="zone__dot" style="background:' + esc(z.color) + '"></span>' + esc(z.label) + '</span><span class="zone__row-note">' + esc(z.note) + "<br>" + p + "</span></div>";
      }).join("");
    });
    $$("[data-zone-map]").forEach(function (el) {
      var zones = (C.zones || []).slice().reverse();
      var radii = [140, 112, 78, 44];
      var rings = zones.map(function (z, i) {
        var r = radii[i] || 30;
        var dashed = z.price === null ? ' stroke-dasharray="6 6" fill-opacity="0.18"' : ' fill-opacity="0.32"';
        return '<circle cx="200" cy="155" r="' + r + '" fill="' + esc(z.color) + '" stroke="' + esc(z.color) + '" stroke-width="1.5"' + dashed + "/>";
      }).join("");
      var labels = zones.map(function (z, i) {
        var r = radii[i] || 30;
        if (i === zones.length - 1) return "";
        return '<text x="200" y="' + (155 - r + 18) + '" text-anchor="middle" font-size="11" font-weight="600" style="fill:var(--muted)">' + esc(z.label) + "</text>";
      }).join("");
      el.innerHTML =
        '<svg viewBox="0 0 400 310" role="img" aria-label="Схема зон выезда: от центра города к пригородам">' +
        '<g stroke="var(--line)" stroke-width="2" fill="none" opacity="0.9"><path d="M20 230 C 120 190, 160 170, 200 155 S 320 90, 390 60"/><path d="M60 30 C 120 90, 170 130, 200 155 S 260 250, 300 300"/><path d="M0 150 H400"/></g>' +
        rings + labels +
        '<g transform="translate(200 145)"><circle r="15" style="fill:var(--surface)"/><path d="M0 9s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" style="fill:var(--primary)"/><circle cy="-2" r="2.6" style="fill:var(--surface)"/></g>' +
        '<text x="200" y="177" text-anchor="middle" font-size="11.5" font-weight="700" style="fill:var(--heading);paint-order:stroke;stroke:var(--surface);stroke-width:3px">' + esc(C.city || "Город") + "</text>" +
        "</svg>";
    });
  }

  /* ---------- 5. Калькулятор ---------- */
  function initCalcs() {
    $$("[data-calc]").forEach(function (root, idx) { new Calc(root, idx); });
  }

  function Calc(root, idx) {
    this.root = root;
    this.uid = "calc" + idx;
    this.state = { step: 1, situation: "vet", species: "cat", weight: "w1", cremation: "individual", pickup: true, urn: true, delivery: false, report: false, zone: (C.zones && C.zones[0] && C.zones[0].id) || "" };
    this.render();
  }
  Calc.prototype.labels = ["Ситуация", "Питомец", "Услуги", "Расчёт"];
  Calc.prototype.render = function () {
    var s = this.state, self = this, u = this.uid;
    var steps = '<ol class="calc__steps">' + this.labels.map(function (l, i) {
      var n = i + 1;
      var cls = n === s.step ? "is-active" : n < s.step ? "is-done" : "";
      return '<li class="calc__step ' + cls + '"' + (n === s.step ? ' aria-current="step"' : "") + '><span class="num">' + (n < s.step ? icon("check") : "0" + n) + '</span><span class="label">' + l + "</span></li>";
    }).join("") + "</ol>";

    var body = "";
    if (s.step === 1) {
      body += '<span class="eyebrow">Начнём с ситуации</span><h3>Какая помощь нужна сейчас?</h3><p class="calc__hint">Это предварительный подбор услуг, а не медицинское решение.</p>';
      body += '<div class="options" role="radiogroup" aria-label="Ситуация">' +
        this.option("radio", "situation", "vet", s.situation === "vet", "steth", "Нужен ветеринар на дом", "Осмотр, разговор и процедура, если вы примете такое решение") +
        this.option("radio", "situation", "died", s.situation === "died", "heart", "Питомец уже умер", "Вывоз тела и кремация") + "</div>";
      body += '<p class="calc__hint">' + icon("chat") + ' Ещё не решили? <button type="button" class="calc-inline-link" data-open="callback" data-topic="Консультация">Получите консультацию</button> — это бесплатно и ни к чему не обязывает.</p>';
    }
    if (s.step === 2) {
      body += '<span class="eyebrow">О питомце</span><h3>Кто ваш питомец?</h3>';
      body += '<div class="options options--sm" role="radiogroup" aria-label="Вид питомца">' + Object.keys(C.species).map(function (k) {
        var sp = C.species[k];
        return self.option("radio", "species", k, s.species === k, sp.icon, sp.short, "", true);
      }).join("") + "</div>";
      var allowed = C.species[s.species].weights;
      if (allowed.length > 1) {
        body += '<div class="calc__group"><span class="calc__group-title">Примерный вес</span><div class="options options--xs" role="radiogroup" aria-label="Вес">' + allowed.map(function (wid) {
          var w = C.weights.filter(function (x) { return x.id === wid; })[0];
          return self.option("radio", "weight", wid, s.weight === wid, "", w.label, "", true);
        }).join("") + "</div></div>";
      } else {
        body += '<p class="calc__hint">Для этого вида питомцев действует одна цена, вес указывать не нужно.</p>';
      }
    }
    if (s.step === 3) {
      body += '<span class="eyebrow">Состав услуг</span><h3>Что нужно организовать?</h3>';
      if (s.situation === "vet") {
        body += '<div class="calc__group"><span class="calc__group-title">Визит врача</span><div class="options">' +
          '<div class="option option--compact" aria-disabled="true"><span class="option__ico">' + icon("steth") + '</span><span class="option__text"><strong>' + esc(C.services.euth.label) + '</strong><small>Входит в расчёт</small></span><span class="option__price">' + rub(C.services.euth.prices[s.weight]) + "</span></div></div></div>";
      }
      var crem = [["individual", C.services.individual], ["common", C.services.common]];
      if (s.situation === "vet") crem.push(["none", { label: "Без кремации", note: "Решу позже или организую сам(а)", prices: null }]);
      body += '<div class="calc__group"><span class="calc__group-title">Кремация</span><div class="options" role="radiogroup" aria-label="Кремация">' + crem.map(function (c) {
        var price = c[1].prices ? rub(c[1].prices[s.weight]) : "";
        return self.option("radio", "cremation", c[0], s.cremation === c[0], c[0] === "none" ? "close" : "flame", c[1].label, c[1].note, false, price);
      }).join("") + "</div></div>";
      if (s.cremation !== "none") {
        var ex = ["pickup"];
        if (s.cremation === "individual") ex = ex.concat(["urn", "delivery", "report"]);
        body += '<div class="calc__group"><span class="calc__group-title">Дополнительно</span><div class="options">' + ex.map(function (k) {
          var e = C.extras[k];
          return self.option("checkbox", k, "1", !!s[k], "", e.label, e.note, false, rub(e.price), true);
        }).join("") + "</div></div>";
      }
      if (C.zones && C.zones.length) {
        body += '<div class="calc__group"><span class="calc__group-title">Где находится питомец</span><div class="options options--sm" role="radiogroup" aria-label="Зона выезда">' + C.zones.map(function (z) {
          var p = z.price === null ? "по договорённости" : z.price === 0 ? "без доплаты" : "+" + rub(z.price);
          return self.option("radio", "zone", z.id, s.zone === z.id, "", z.label, p, true);
        }).join("") + "</div></div>";
      }
    }
    if (s.step === 4) {
      var r = this.calcTotal();
      body += '<span class="eyebrow">Предварительный расчёт</span><h3>Ориентировочная стоимость</h3>';
      body += '<div class="calc-summary">' + r.rows.map(function (row) {
        return '<div class="calc-summary__row' + (row.muted ? " calc-summary__row--muted" : "") + '"><span>' + esc(row.label) + "</span><span>" + row.value + "</span></div>";
      }).join("") + '<div class="calc-summary__total"><span>Итого' + (r.approx ? ", от" : "") + '</span><strong>' + rub(r.total) + "</strong></div></div>";
      body += '<p class="calc__hint">Окончательную стоимость подтвердим по телефону и до начала работы. Расчёт не является публичной офертой.' + (C.demoPrices ? ' <span class="badge">Демо-цены</span>' : "") + "</p>";
      body += '<div class="btn-row"><button type="button" class="btn btn--primary" data-open="callback" data-topic="Расчёт стоимости" data-comment="' + esc(r.summary) + '">' + icon("phone") + "Обсудить расчёт</button><button type=\"button\" class=\"btn\" data-calc-restart>" + icon("arrow-left") + "Пересчитать</button></div>";
    }

    var foot = '<div class="calc__foot"><button type="button" class="btn btn--sm" data-calc-back' + (s.step === 1 ? " disabled" : "") + ">" + icon("arrow-left") + 'Назад</button><span class="calc__counter">Шаг ' + s.step + " из 4</span>" +
      (s.step < 4 ? '<button type="button" class="btn btn--primary btn--sm" data-calc-next>' + (s.step === 3 ? "Показать расчёт" : "Продолжить") + icon("arrow-right") + "</button>" : '<span style="width:96px"></span>') + "</div>";

    this.root.innerHTML = '<div class="calc">' + steps + '<div class="calc__body" aria-live="polite">' + body + "</div>" + foot + "</div>" +
      '<p class="calc__privacy">' + icon("lock") + "Расчёт выполняется в браузере. Чтобы увидеть сумму, контакты оставлять не нужно.</p>";
    this.bind();
  };
  Calc.prototype.option = function (type, name, value, checked, ico, title, sub, compact, price, row) {
    var id = this.uid + "-" + name + "-" + value;
    return '<label class="option' + (compact ? " option--compact" : "") + (row ? " option--row" : "") + '" for="' + id + '">' +
      '<input type="' + type + '" id="' + id + '" name="' + this.uid + "-" + name + '" value="' + value + '"' + (checked ? " checked" : "") + ' data-key="' + name + '">' +
      (ico ? '<span class="option__ico">' + icon(ico) + "</span>" : "") +
      '<span class="option__text"><strong>' + esc(title) + "</strong>" + (sub ? "<small>" + esc(sub) + "</small>" : "") + "</span>" +
      (price ? '<span class="option__price">' + price + "</span>" : "") +
      '<span class="option__check">' + icon("check") + "</span></label>";
  };
  Calc.prototype.bind = function () {
    var self = this, s = this.state;
    $$("input[data-key]", this.root).forEach(function (inp) {
      inp.addEventListener("change", function () {
        var k = inp.getAttribute("data-key");
        if (inp.type === "checkbox") s[k] = inp.checked; else s[k] = inp.value;
        if (k === "species") {
          var allowed = C.species[s.species].weights;
          if (allowed.indexOf(s.weight) === -1) s.weight = allowed[0];
          self.render(); self.focusFirst();
        }
        if (k === "situation") {
          if (s.situation === "died" && s.cremation === "none") s.cremation = "individual";
          s.pickup = true;
        }
        if (k === "cremation") {
          if (s.cremation === "individual") s.urn = true;
          self.render(); self.focusFirst();
        }
      });
    });
    var next = $("[data-calc-next]", this.root), back = $("[data-calc-back]", this.root), restart = $("[data-calc-restart]", this.root);
    if (next) next.addEventListener("click", function () { s.step = Math.min(4, s.step + 1); self.render(); self.focusFirst(); });
    if (back) back.addEventListener("click", function () { s.step = Math.max(1, s.step - 1); self.render(); self.focusFirst(); });
    if (restart) restart.addEventListener("click", function () { s.step = 1; self.render(); self.focusFirst(); });
  };
  Calc.prototype.focusFirst = function () {
    var h = $(".calc__body h3", this.root);
    if (h) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); }
  };
  Calc.prototype.calcTotal = function () {
    var s = this.state, rows = [], total = 0, approx = false, parts = [];
    var sp = C.species[s.species];
    var w = C.weights.filter(function (x) { return x.id === s.weight; })[0];
    var petLabel = sp.short + (sp.weights.length > 1 ? ", " + w.label : "");
    rows.push({ label: "Питомец", value: esc(petLabel), muted: true });
    parts.push("Питомец: " + petLabel);
    var add = function (label, price) { rows.push({ label: label, value: rub(price) }); total += price; parts.push(label + " — " + rub(price)); };
    if (s.situation === "vet") add(C.services.euth.label, C.services.euth.prices[s.weight]);
    if (s.cremation !== "none") {
      add(C.services[s.cremation].label, C.services[s.cremation].prices[s.weight]);
      ["pickup", "urn", "delivery", "report"].forEach(function (k) {
        if (!s[k]) return;
        if (k !== "pickup" && s.cremation !== "individual") return;
        add(C.extras[k].label, C.extras[k].price);
      });
    }
    var z = (C.zones || []).filter(function (x) { return x.id === s.zone; })[0];
    if (z) {
      if (z.price === null) { rows.push({ label: "Выезд: " + z.label, value: "по договорённости", muted: true }); approx = true; parts.push("Выезд: " + z.label + " — по договорённости"); }
      else if (z.price === 0) { rows.push({ label: "Выезд: " + z.label, value: "без доплаты", muted: true }); parts.push("Выезд: " + z.label); }
      else add("Выезд: " + z.label, z.price);
    }
    parts.push("Итого: " + (approx ? "от " : "") + rub(total));
    return { rows: rows, total: total, approx: approx, summary: parts.join("; ") };
  };

  /* ---------- 6. Слайдер ---------- */
  function initSliders() {
    $$("[data-slider]").forEach(function (box) {
      var track = $(".slider__track", box);
      var prev = $("[data-slider-prev]", box.parentNode.parentNode) || $("[data-slider-prev]", box);
      var next = $("[data-slider-next]", box.parentNode.parentNode) || $("[data-slider-next]", box);
      if (!track) return;
      var step = function () { var c = track.children[0]; return c ? c.getBoundingClientRect().width + 20 : 300; };
      var update = function () {
        if (prev) prev.disabled = track.scrollLeft <= 4;
        if (next) next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
      };
      if (prev) prev.addEventListener("click", function () { track.scrollBy({ left: -step(), behavior: "smooth" }); });
      if (next) next.addEventListener("click", function () { track.scrollBy({ left: step(), behavior: "smooth" }); });
      track.addEventListener("scroll", function () { window.requestAnimationFrame(update); }, { passive: true });
      window.addEventListener("resize", update);
      update();
    });
  }

  /* ---------- 7. Формы ---------- */
  function formatPhone(v) {
    var d = v.replace(/\D/g, "");
    if (!d) return "";
    if (d[0] === "8") d = "7" + d.slice(1);
    if (d[0] !== "7") d = "7" + d;
    d = d.slice(0, 11);
    var out = "+7";
    if (d.length > 1) out += " (" + d.slice(1, 4);
    if (d.length >= 4) out += ")";
    if (d.length > 4) out += " " + d.slice(4, 7);
    if (d.length > 7) out += "-" + d.slice(7, 9);
    if (d.length > 9) out += "-" + d.slice(9, 11);
    return out;
  }
  function initForms() {
    $$("input[type=tel]").forEach(function (inp) {
      inp.addEventListener("input", function () { inp.value = formatPhone(inp.value); });
      inp.addEventListener("focus", function () { if (!inp.value) inp.value = "+7 ("; });
      inp.addEventListener("blur", function () { if (inp.value.replace(/\D/g, "").length <= 1) inp.value = ""; });
    });
    $$("form[data-form]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var ok = true;
        $$(".field", form).forEach(function (f) { f.classList.remove("is-invalid"); var er = $(".field__error", f); if (er) er.textContent = ""; });
        var tel = $("input[type=tel]", form);
        if (tel && tel.required && tel.value.replace(/\D/g, "").length !== 11) {
          ok = false; var f = tel.closest(".field"); f.classList.add("is-invalid"); $(".field__error", f).textContent = "Введите номер полностью: +7 и ещё 10 цифр.";
        }
        $$("[required]:not([type=tel]):not([type=checkbox])", form).forEach(function (inp) {
          if (!inp.value.trim()) { ok = false; var f = inp.closest(".field"); if (f) { f.classList.add("is-invalid"); var er = $(".field__error", f); if (er) er.textContent = "Заполните это поле."; } }
        });
        var consent = $("input[name=consent]", form);
        var cl = consent && consent.closest(".consent");
        if (cl) cl.classList.remove("is-invalid");
        if (consent && !consent.checked) { ok = false; cl.classList.add("is-invalid"); }
        if (!ok) { var first = $(".is-invalid input, .is-invalid textarea, .consent.is-invalid input", form); if (first) first.focus(); return; }

        var data = {};
        new FormData(form).forEach(function (v, k) { data[k] = v; });
        data.form = form.getAttribute("data-form");
        data.page = location.pathname;
        var status = $(".form-status", form);
        var btn = $("button[type=submit]", form);
        var done = function (title, text, good) {
          status.hidden = false;
          status.innerHTML = icon(good ? "check" : "info") + "<div><strong>" + esc(title) + "</strong>" + esc(text) + "</div>";
        };
        if (C.formEndpoint) {
          btn.disabled = true;
          fetch(C.formEndpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
            .then(function (r) { if (!r.ok) throw new Error(r.status); form.reset(); done("Заявка отправлена", "Мы свяжемся с вами в ближайшее время.", true); })
            .catch(function () { done("Не получилось отправить заявку", "Пожалуйста, позвоните нам: " + (C.phone || ""), false); })
            .then(function () { btn.disabled = false; });
        } else {
          form.reset();
          done("Демо-режим: заявка не отправлена", " Форма проверена и работает, но обработчик ещё не подключён. Укажите formEndpoint в config.js.", true);
        }
      });
    });
  }

  /* ---------- 8. Модальные окна ---------- */
  function initModals() {
    document.addEventListener("click", function (e) {
      var opener = e.target.closest("[data-open]");
      if (!opener) return;
      var id = opener.getAttribute("data-open");
      var dlg = document.getElementById(id + "-modal");
      if (!dlg || typeof dlg.showModal !== "function") return;
      e.preventDefault();
      if (window.__closeMobileMenu) window.__closeMobileMenu();
      var topic = opener.getAttribute("data-topic");
      var comment = opener.getAttribute("data-comment");
      var sel = $("select[name=topic]", dlg);
      if (sel && topic) { var has = $$("option", sel).some(function (o) { return o.value === topic; }); if (has) sel.value = topic; }
      var ta = $("textarea[name=comment]", dlg);
      if (ta && comment) ta.value = comment;
      var st = $(".form-status", dlg); if (st) st.hidden = true;
      dlg.showModal();
      var focusEl = $("input:not([type=hidden])", dlg); if (focusEl) setTimeout(function () { focusEl.focus(); }, 30);
      if (id === "search") runSearch("");
    });
    $$("dialog").forEach(function (dlg) {
      dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
      $$("[data-close]", dlg).forEach(function (b) { b.addEventListener("click", function () { dlg.close(); }); });
    });
  }

  /* ---------- 9. Поиск по сайту ---------- */
  var INDEX = [
    { t: "Главная", u: "index.html", d: "Усыпление на дому и кремация животных", k: "главная служба" },
    { t: "Усыпление на дому", u: "usyplenie.html", d: "Как проходит визит врача, показания, подготовка", k: "эвтаназия усыпить усыпление врач на дом" },
    { t: "Усыпление кошек", u: "usyplenie.html#koshki", d: "Особенности визита для кошек", k: "кошка кот усыпить кошку" },
    { t: "Усыпление собак", u: "usyplenie.html#sobaki", d: "Крупные и пожилые собаки", k: "собака пёс пес усыпить собаку" },
    { t: "Грызуны, кролики, хорьки", u: "usyplenie.html#gryzuny", d: "Хомяки, крысы, морские свинки, кролики", k: "хомяк крыса свинка кролик хорёк хорек грызун" },
    { t: "Птицы и экзотические животные", u: "usyplenie.html#pticy", d: "Попугаи, рептилии, черепахи", k: "птица попугай рептилия черепаха экзотика ящерица змея" },
    { t: "Как подготовиться к визиту", u: "usyplenie.html#podgotovka", d: "Что сделать до приезда врача", k: "подготовка подготовиться приезд" },
    { t: "Кремация животных", u: "kremaciya.html", d: "Общая и индивидуальная кремация", k: "кремация кремировать прах крематорий" },
    { t: "Индивидуальная кремация", u: "kremaciya.html#individualnaya", d: "Прах возвращается в урне", k: "индивидуальная прах урна" },
    { t: "Общая кремация", u: "kremaciya.html#obshchaya", d: "Без возврата праха", k: "общая групповая" },
    { t: "Вывоз тела животного", u: "kremaciya.html#vyvoz", d: "Заберём питомца из дома или клиники", k: "вывоз забрать тело умер умерла" },
    { t: "Урны для праха", u: "kremaciya.html#urny", d: "Выбор урны и доставка", k: "урна доставка праха" },
    { t: "Фото- и видеоотчёт", u: "kremaciya.html#otchet", d: "Подтверждение индивидуальной кремации", k: "фото видео отчёт отчет подтверждение" },
    { t: "Цены", u: "ceny.html", d: "Прайс по видам питомцев и весу", k: "цена стоимость прайс сколько стоит" },
    { t: "Калькулятор стоимости", u: "ceny.html#kalkulyator", d: "Предварительный расчёт за 4 шага", k: "калькулятор расчёт рассчитать" },
    { t: "О службе", u: "o-nas.html", d: "Принципы работы и врачи", k: "о нас служба врачи команда" },
    { t: "Зона выезда", u: "zona.html", d: "Город и пригороды, доплаты за выезд", k: "зона выезд география район пригород" },
    { t: "Полезная информация", u: "stati.html", d: "Памятки для владельцев", k: "статьи памятки советы" },
    { t: "Как подготовиться к визиту ветеринара", u: "stati-podgotovka.html", d: "Памятка владельцу", k: "подготовка визит место прощание" },
    { t: "Общая или индивидуальная кремация", u: "stati-kremaciya.html", d: "Как выбрать формат", k: "выбрать кремацию разница" },
    { t: "Питомец умер дома: что делать", u: "stati-pitomec-umer.html", d: "Первые часы: пошагово", k: "умер умерла дома ночью что делать" },
    { t: "Как пережить уход питомца", u: "stati-poterya.html", d: "Горе, чувство вины, разговор с детьми", k: "горе утрата дети вина поддержка" },
    { t: "Вопросы и ответы", u: "faq.html", d: "Ответы на частые вопросы", k: "вопрос ответ faq больно сколько длится" },
    { t: "Отзывы", u: "otzyvy.html", d: "Обратная связь владельцев", k: "отзыв отзывы обратная связь" },
    { t: "Контакты", u: "kontakty.html", d: "Телефон, почта, режим работы", k: "контакты телефон почта связаться" },
    { t: "Политика конфиденциальности", u: "privacy.html", d: "Обработка персональных данных", k: "политика персональные данные конфиденциальность" }
  ];
  function runSearch(q) {
    var list = $("#search-results");
    if (!list) return;
    q = q.trim().toLowerCase();
    var res = !q ? INDEX.slice(0, 8) : INDEX.filter(function (i) { return (i.t + " " + i.d + " " + i.k).toLowerCase().indexOf(q) !== -1; });
    list.innerHTML = res.length ? res.map(function (i) { return '<li><a href="' + i.u + '"><strong>' + esc(i.t) + "</strong><small>" + esc(i.d) + "</small></a></li>"; }).join("") : '<li class="search-empty">Ничего не нашли. Попробуйте другое слово или позвоните нам — подскажем.</li>';
  }
  function initSearch() {
    var inp = $("#search-input");
    if (!inp) return;
    inp.addEventListener("input", function () { runSearch(inp.value); });
    $$("#search-results").forEach(function (l) { l.addEventListener("click", function (e) { if (e.target.closest("a")) { var d = $("#search-modal"); if (d) d.close(); } }); });
  }

  /* ---------- 10. Прочее ---------- */
  function initToTop() {
    var b = $(".to-top");
    if (!b) return;
    window.addEventListener("scroll", function () { b.classList.toggle("is-visible", window.scrollY > 700); }, { passive: true });
    b.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }
  function initSubnav() {
    var links = $$(".subnav a[href^='#']");
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    links.forEach(function (a) { var t = document.getElementById(a.getAttribute("href").slice(1)); if (t) map[t.id] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { links.forEach(function (l) { l.classList.remove("is-active"); }); var a = map[en.target.id]; if (a) a.classList.add("is-active"); }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(map).forEach(function (id) { io.observe(document.getElementById(id)); });
  }
  function initFilters() {
    var btns = $$("[data-filter]");
    if (!btns.length) return;
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        var f = b.getAttribute("data-filter");
        btns.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        $$("[data-cat]").forEach(function (card) { card.hidden = f !== "all" && card.getAttribute("data-cat") !== f; });
      });
    });
  }
  function initHash() {
    if (!location.hash) return;
    var el = document.getElementById(location.hash.slice(1));
    if (!el) return;
    if (el.tagName === "DETAILS") el.open = true;
    // Цены и калькулятор дорисовываются скриптом — после этого возвращаемся к якорю
    window.addEventListener("load", function () { el.scrollIntoView({ block: "start" }); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyConfig();
    initHeader();
    renderPriceTables();
    renderZones();
    initCalcs();
    initSliders();
    initForms();
    initModals();
    initSearch();
    initToTop();
    initSubnav();
    initFilters();
    initHash();
  });
})();
