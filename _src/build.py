#!/usr/bin/env python3
"""Сборка статического сайта «Мягкий Свет».

Страницы лежат в _src/pages/*.html. Первая строка каждой страницы —
JSON с метаданными: {"title": ..., "description": ..., "nav": ..., "out": ...}.
Шорткоды в тексте страниц:
  {{i:name}}       — иконка из спрайта
  {{part:name}}    — общий блок из PARTS ниже
Запуск: python3 _src/build.py  → результат в site/
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
OUT = ROOT / "site"
SITE_URL = "https://diego001-art.github.io/Vet/"  # адрес сайта; поменяйте, если подключите свой домен
VER = time.strftime("%Y%m%d%H%M")  # версия для сброса кеша браузера

BRAND = "Мягкий Свет"
TAGLINE = "Ветеринарная служба деликатной помощи"

# Значения-заглушки. Реальные данные подставляет assets/js/config.js
PH = {
    "phone": "+7 (000) 000-00-00",
    "phoneHref": "+70000000000",
    "email": "info@example.com",
    "hours": "Часы работы уточняются",
    "city": "Ваш город",
    "region": "и пригороды",
}


def icon(name, cls="icon"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


# --------------------------------------------------------------------------
# Иконки (линейные, 24×24)
# --------------------------------------------------------------------------
ICONS = {
    "phone": '<path d="M5 4h3l2 5-2.5 1.5a11 11 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "chat": '<path d="M21 12a8.5 8.5 0 0 1-12.3 7.6L4 20.5l1.1-4.4A8.5 8.5 0 1 1 21 12z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>',
    "calc": '<rect x="5" y="3" width="14" height="18" rx="2.5"/><path d="M8.5 7h7M8.5 11h.01M12 11h.01M15.5 11h.01M8.5 14.5h.01M12 14.5h.01M15.5 14.5h.01M8.5 18h.01M12 18h.01M15.5 18h.01"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "steth": '<path d="M6 3H5v5a4.5 4.5 0 0 0 9 0V3h-1"/><path d="M9.5 12.5V15a5 5 0 0 0 10 0v-2"/><circle cx="19.5" cy="11" r="2"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "heart": '<path d="M12 20s-7.5-4.6-9.2-9.4A4.9 4.9 0 0 1 12 7a4.9 4.9 0 0 1 9.2 3.6C19.5 15.4 12 20 12 20z"/>',
    "home": '<path d="M4 11l8-7 8 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/>',
    "truck": '<path d="M3 6h11v10H3zM14 9h4l3 3.5V16h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17.5" cy="18" r="2"/>',
    "urn": '<path d="M8 3.5h8M9.5 3.5V6A4.5 4.5 0 0 0 6 10.5c0 4 2 7 3 9h6c1-2 3-5 3-9A4.5 4.5 0 0 0 14.5 6V3.5"/><path d="M7 20.5h10M8 11h8"/>',
    "flame": '<path d="M12 21a6.5 6.5 0 0 0 6.5-6.5c0-4.3-3.3-6.3-4.5-10.5-2 2-3 4-3 6.2-1-1-1.8-2.1-2-3.7C7 8.6 5.5 11.4 5.5 14.5A6.5 6.5 0 0 0 12 21z"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "arrow-left": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "arrow-up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "paw": '<circle cx="6.5" cy="10" r="1.9"/><circle cx="10" cy="6" r="1.9"/><circle cx="14" cy="6" r="1.9"/><circle cx="17.5" cy="10" r="1.9"/><path d="M12 11.5c-2.8 0-5.6 3.6-5.6 5.9 0 1.5 1.2 2.4 2.8 2.4 1.2 0 1.8-.6 2.8-.6s1.6.6 2.8.6c1.6 0 2.8-.9 2.8-2.4 0-2.3-2.8-5.9-5.6-5.9z"/>',
    "cat": '<path d="M4.5 4l3.8 3.3h7.4L19.5 4v8a7.5 7.5 0 0 1-15 0z"/><path d="M9.3 12h.01M14.7 12h.01M11 15.2l1 .9 1-.9"/>',
    "dog": '<path d="M7.5 5.5h9L20 7l-.8 5.2-2-.6V14a5.2 5.2 0 0 1-10.4 0v-2.4l-2 .6L4 7z"/><path d="M9.6 11.3h.01M14.4 11.3h.01M11 15h2l-1 1.2z"/>',
    "rodent": '<path d="M3.5 17.5c0-4.4 3.7-7.5 8-7.5 2.7 0 4.6 1.2 5.7 2.8l2.8 1-.7 3.2-1.6.5z"/><circle cx="11.5" cy="8.3" r="2.2"/><path d="M15.6 14.3h.01M3.5 17.5c-1 .8-1 2.6.6 2.8"/>',
    "bird": '<path d="M4 14.5c3 0 5-2.2 6-5.3a4 4 0 0 1 7.8-.7L21 10l-3 1v1c0 4.3-3.2 7.5-8 7.5H6l2-2.2c-2 0-3.2-1-4-2.8z"/><path d="M14.6 8.4h.01"/>',
    "turtle": '<path d="M4.5 15a7.5 6.5 0 0 1 15 0z"/><path d="M3 15h18M19.5 13H21a1.6 1.6 0 0 1 0 3.2h-1.2M7 15v3M17 15v3M9 10.5l3 2 3-2"/>',
    "shield": '<path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3.5 7l8.5 6 8.5-6"/>',
    "calendar": '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
    "book": '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3"/>',
    "leaf": '<path d="M5 19c0-8.5 5.5-14 15-14 0 9.5-5.5 15-14 15"/><path d="M5 19l7.5-7.5"/>',
    "hand": '<path d="M7.5 11.5V6a1.5 1.5 0 0 1 3 0v4.5M10.5 10.5V4.5a1.5 1.5 0 0 1 3 0v6M13.5 10.5V5.5a1.5 1.5 0 0 1 3 0V11M16.5 11V8.5a1.5 1.5 0 0 1 3 0v5.5a7 7 0 0 1-7 7h-.8a6 6 0 0 1-5-2.7l-3-4.6a1.6 1.6 0 0 1 2.6-1.9l1.2 1.4"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "map": '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "photo": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.6"/><path d="M21 16l-5-5-8.5 8"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6L6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.3-4.1 5.9-.9z"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M15.5 4.8a3.5 3.5 0 0 1 0 6.4M18 14.2a6.5 6.5 0 0 1 3.5 5.8"/>',
    "route": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h6.5"/>',
}

SPRITE = '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">' + "".join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()
) + "</svg>"


def emblem(uid, size=46, cls="brand__mark"):
    """Эмблема: арка окна, лапа и тёплый огонёк."""
    return f'''<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="g-{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2d9ad0"/><stop offset="1" stop-color="#22598c"/></linearGradient></defs><path d="M8 30a24 24 0 0 1 48 0v24a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6z" fill="url(#g-{uid})"/><circle cx="32" cy="17.5" r="8.5" fill="#f2b56b" opacity=".25"/><circle cx="32" cy="17.5" r="4.6" fill="#f2b56b"/><g fill="#fff"><ellipse cx="21.6" cy="34.4" rx="3.3" ry="4.1" transform="rotate(-24 21.6 34.4)"/><ellipse cx="27.6" cy="29" rx="3.4" ry="4.4" transform="rotate(-8 27.6 29)"/><ellipse cx="36.4" cy="29" rx="3.4" ry="4.4" transform="rotate(8 36.4 29)"/><ellipse cx="42.4" cy="34.4" rx="3.3" ry="4.1" transform="rotate(24 42.4 34.4)"/><path d="M32 37c-4.6 0-9.5 5.6-9.5 9.6 0 2.6 2 4 4.6 4 2 0 3.2-1 4.9-1s2.9 1 4.9 1c2.6 0 4.6-1.4 4.6-4 0-4-4.9-9.6-9.5-9.6z"/></g></svg>'''


def brand(uid, href="index.html"):
    return f'''<a class="brand" href="{href}" aria-label="{BRAND} — на главную">{emblem(uid)}<span class="brand__text"><span class="brand__name">{BRAND}</span><span class="brand__tag">{TAGLINE}</span></span></a>'''


def phone_link(cls, inner):
    return f'<a class="{cls}" href="tel:{PH["phoneHref"]}" data-site-href="tel">{inner}</a>'


PHONE_TXT = f'<span data-site="phone">{PH["phone"]}</span>'
HOURS_TXT = f'<span data-site="hours">{PH["hours"]}</span>'
CITY_TXT = f'<span data-site="city">{PH["city"]}</span>'
REGION_TXT = f'<span data-site="region">{PH["region"]}</span>'
EMAIL_LINK = f'<a href="mailto:{PH["email"]}" data-site-href="mailto"><span data-site="email">{PH["email"]}</span></a>'

# --------------------------------------------------------------------------
# Навигация
# --------------------------------------------------------------------------
NAV = [
    {
        "id": "usyplenie", "label": "Усыпление", "href": "usyplenie.html",
        "cols": [
            ("По видам питомцев", [("cat", "Кошки и коты", "usyplenie.html#koshki"), ("dog", "Собаки", "usyplenie.html#sobaki"), ("rodent", "Грызуны, кролики, хорьки", "usyplenie.html#gryzuny"), ("bird", "Птицы", "usyplenie.html#pticy"), ("turtle", "Рептилии и экзотика", "usyplenie.html#pticy")]),
            ("Перед визитом", [("info", "Когда обсуждают эвтаназию", "usyplenie.html#kogda"), ("steth", "Как проходит визит врача", "usyplenie.html#vizit"), ("home", "Как подготовиться", "usyplenie.html#podgotovka"), ("book", "Памятка: подготовка к визиту", "stati-podgotovka.html")]),
        ],
        "promo": ("Стоимость усыпления", "Цена зависит от вида и веса питомца. Посмотрите прайс или посчитайте в калькуляторе.", [("ceny.html#prajs", "Смотреть цены"), ("ceny.html#kalkulyator", "Калькулятор")]),
    },
    {
        "id": "kremaciya", "label": "Кремация", "href": "kremaciya.html",
        "cols": [
            ("Форматы", [("flame", "Индивидуальная кремация", "kremaciya.html#individualnaya"), ("users", "Общая кремация", "kremaciya.html#obshchaya"), ("doc", "Сравнение форматов", "kremaciya.html#sravnenie")]),
            ("Сопутствующие услуги", [("truck", "Вывоз тела", "kremaciya.html#vyvoz"), ("urn", "Урны для праха", "kremaciya.html#urny"), ("route", "Доставка урны", "kremaciya.html#urny"), ("camera", "Фото- и видеоотчёт", "kremaciya.html#otchet")]),
        ],
        "promo": ("Питомец умер дома?", "Расскажем, что сделать в первые часы, и организуем вывоз на кремацию.", [("stati-pitomec-umer.html", "Читать памятку")]),
    },
    {
        "id": "ceny", "label": "Цены", "href": "ceny.html",
        "cols": [
            ("Стоимость", [("doc", "Прайс по видам и весу", "ceny.html#prajs"), ("info", "Что оплачивается отдельно", "ceny.html#otdelno"), ("calc", "Калькулятор стоимости", "ceny.html#kalkulyator"), ("chat", "Вопросы о ценах", "ceny.html#voprosy")]),
        ],
        "promo": ("Точная сумма — до начала работы", "Оператор назовёт стоимость по телефону, врач подтвердит её на месте.", [("kontakty.html", "Связаться")]),
    },
    {
        "id": "o-nas", "label": "О службе", "href": "o-nas.html",
        "cols": [
            ("Служба", [("heart", "Наши принципы", "o-nas.html#principy"), ("steth", "Врачи", "o-nas.html#vrachi"), ("shield", "Как мы работаем", "o-nas.html#rabota"), ("map", "Зона выезда", "zona.html")]),
            ("Связь", [("star", "Отзывы", "otzyvy.html"), ("phone", "Контакты", "kontakty.html"), ("lock", "Конфиденциальность", "privacy.html")]),
        ],
        "promo": None,
    },
    {"id": "zona", "label": "Зона выезда", "href": "zona.html"},
    {
        "id": "stati", "label": "Полезное", "href": "stati.html",
        "cols": [
            ("Памятки владельцу", [("home", "Как подготовиться к визиту врача", "stati-podgotovka.html"), ("flame", "Общая или индивидуальная кремация", "stati-kremaciya.html"), ("heart", "Питомец умер дома: что делать", "stati-pitomec-umer.html"), ("leaf", "Как пережить уход питомца", "stati-poterya.html")]),
            ("Справка", [("book", "Все материалы", "stati.html"), ("chat", "Вопросы и ответы", "faq.html")]),
        ],
        "promo": None,
    },
    {"id": "otzyvy", "label": "Отзывы", "href": "otzyvy.html"},
    {"id": "kontakty", "label": "Контакты", "href": "kontakty.html"},
]


def desktop_nav(active):
    items = []
    for n in NAV:
        cur = " is-current" if n["id"] == active else ""
        if "cols" not in n:
            aria = ' aria-current="page"' if n["id"] == active else ""
            items.append(f'<li class="nav__item{cur}"><a class="nav__link" href="{n["href"]}"{aria}>{n["label"]}</a></li>')
            continue
        cols = ""
        for title, links in n["cols"]:
            lis = "".join(f'<li><a href="{h}">{icon(ic)}{t}</a></li>' for ic, t, h in links)
            cols += f'<div class="mega__col"><h4>{title}</h4><ul>{lis}</ul></div>'
        cols += f'<div class="mega__col"><h4>Раздел</h4><ul><li><a href="{n["href"]}">{icon("arrow-right")}Перейти в раздел «{n["label"]}»</a></li></ul></div>' if not n.get("promo") else ""
        if n.get("promo"):
            t, p, links = n["promo"]
            btns = "".join(f'<a class="link-arrow" href="{h}">{l}{icon("arrow-right")}</a>' for h, l in links)
            cols += f'<div class="mega__promo"><strong>{t}</strong><p>{p}</p>{btns}</div>'
        ncols = len(n["cols"]) + 1
        items.append(
            f'<li class="nav__item has-mega{cur}"><button class="nav__link" type="button" aria-expanded="false" aria-controls="mega-{n["id"]}">{n["label"]}{icon("chev", "icon chev")}</button>'
            f'<div class="mega" id="mega-{n["id"]}"><div class="container mega__inner" style="--cols:{ncols}">{cols}</div></div></li>'
        )
    return "".join(items)


def mobile_nav(active):
    items = []
    for n in NAV:
        if "cols" not in n:
            items.append(f'<li><a class="m-nav__link" href="{n["href"]}">{n["label"]}</a></li>')
            continue
        sub = f'<li><a href="{n["href"]}"><strong>Весь раздел «{n["label"]}»</strong></a></li>'
        for title, links in n["cols"]:
            sub += f'<li class="m-nav__group">{title}</li>' + "".join(f'<li><a href="{h}">{t}</a></li>' for _, t, h in links)
        items.append(
            f'<li><button class="m-nav__link" type="button" aria-expanded="false" aria-controls="m-{n["id"]}">{n["label"]}{icon("chev", "icon chev")}</button>'
            f'<ul class="m-nav__sub" id="m-{n["id"]}" hidden>{sub}</ul></li>'
        )
    return "".join(items)


def header(active):
    return f'''<a class="skip-link" href="#main">Перейти к содержимому</a>
<header class="site-header">
  <div class="container topbar">
    {brand("h")}
    <div class="topbar__region">{icon("pin")}<span><strong>{CITY_TXT}</strong>{REGION_TXT}</span></div>
    <span class="topbar__spacer"></span>
    {phone_link("topbar__phone", f'<span class="topbar__phone-ico">{icon("phone")}</span><span class="topbar__phone-num">{PHONE_TXT}<small>{HOURS_TXT}</small></span>')}
    <button class="btn btn--primary btn--sm topbar__cta" type="button" data-open="callback" data-topic="Выезд ветеринара">{icon("chat")}Вызвать врача</button>
    <button class="icon-btn icon-btn--primary topbar__chat" type="button" data-open="callback" data-topic="Выезд ветеринара" aria-label="Оставить заявку">{icon("chat")}</button>
    <button class="icon-btn topbar__burger" type="button" aria-expanded="false" aria-controls="mobile-menu" aria-label="Открыть меню">{icon("menu")}</button>
  </div>
  <nav class="navbar" aria-label="Основное меню">
    <div class="container nav">
      <ul class="nav__list">{desktop_nav(active)}</ul>
      <button class="nav__search" type="button" data-open="search" aria-label="Поиск по сайту">{icon("search")}</button>
    </div>
  </nav>
</header>
<div class="nav-backdrop" aria-hidden="true"></div>
<div class="mobile-menu" id="mobile-menu">
  <nav aria-label="Мобильное меню"><ul class="m-nav">{mobile_nav(active)}
    <li><button class="m-nav__link" type="button" data-open="search">Поиск по сайту{icon("search")}</button></li></ul></nav>
  <div class="mobile-menu__contacts">
    {phone_link("btn btn--primary btn--block", icon("phone") + PHONE_TXT)}
    <p class="small muted">{icon("clock")} {HOURS_TXT} · {CITY_TXT} {REGION_TXT}</p>
  </div>
</div>'''


FOOTER_COLS = [
    ("Услуги", [("Усыпление на дому", "usyplenie.html"), ("Индивидуальная кремация", "kremaciya.html#individualnaya"), ("Общая кремация", "kremaciya.html#obshchaya"), ("Вывоз тела", "kremaciya.html#vyvoz"), ("Урны для праха", "kremaciya.html#urny")]),
    ("Служба", [("О службе", "o-nas.html"), ("Врачи", "o-nas.html#vrachi"), ("Цены", "ceny.html"), ("Калькулятор", "ceny.html#kalkulyator"), ("Зона выезда", "zona.html")]),
    ("Информация", [("Полезное", "stati.html"), ("Вопросы и ответы", "faq.html"), ("Отзывы", "otzyvy.html"), ("Контакты", "kontakty.html"), ("Конфиденциальность", "privacy.html")]),
]


def footer():
    cols = "".join(
        f'<div><h4>{t}</h4><ul>' + "".join(f'<li><a href="{h}">{l}</a></li>' for l, h in links) + "</ul></div>"
        for t, links in FOOTER_COLS
    )
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer__top">
      <div class="footer__about">
        {brand("f")}
        <p>Выездная ветеринарная помощь, бережное прощание и кремация домашних животных.</p>
      </div>
      <nav class="footer__nav" aria-label="Меню в подвале">{cols}</nav>
      <div class="footer__contacts">
        {phone_link("footer__phone", PHONE_TXT)}
        {HOURS_TXT}
        <span>{EMAIL_LINK}</span>
        <span data-site-block="address" hidden>{icon("pin")} <span data-site="address"></span></span>
        <div class="footer__social" data-site-block="messengers" hidden><div class="chip-row" data-site-list="messengers"></div></div>
        <div class="footer__social" data-site-block="socials" hidden><div class="chip-row" data-site-list="socials"></div></div>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© <span data-year>2026</span> {BRAND}. {TAGLINE}.</span>
      <span><a href="privacy.html">Политика конфиденциальности</a></span>
      <span class="footer__motto">Рядом, когда это важнее всего</span>
    </div>
    <p class="footer__legal">Информация на сайте носит справочный характер и не является публичной офертой. Стоимость услуг подтверждается до начала их оказания.</p>
    <p class="footer__legal" data-site-block="legal" hidden><span data-site="legal"></span></p>
  </div>
</footer>
<div class="callbar">
  {phone_link("btn btn--primary", icon("phone") + '<span>Позвонить</span>')}
  <button class="btn btn--ghost" type="button" data-open="callback" data-topic="Выезд ветеринара">{icon("chat")}<span class="hide-xs">Заявка</span></button>
</div>
<button class="to-top" type="button" aria-label="Наверх">{icon("arrow-up")}</button>'''


TOPICS = ["Консультация", "Выезд ветеринара", "Усыпление на дому", "Индивидуальная кремация", "Общая кремация", "Вывоз тела", "Расчёт стоимости", "Другое"]


def form_fields(prefix, topic_default="Консультация", title="Заказать обратный звонок", sub="Оставьте номер — перезвоним, ответим на вопросы и согласуем время визита.", name="callback"):
    opts = "".join(f'<option{" selected" if t == topic_default else ""}>{t}</option>' for t in TOPICS)
    return f'''<form class="form-card" data-form="{name}" novalidate>
      <h3>{title}</h3>
      <p>{sub}</p>
      <div class="form-grid">
        <div class="field"><label for="{prefix}-name">Как к вам обращаться</label><input class="input" id="{prefix}-name" name="name" type="text" autocomplete="name" placeholder="Имя"><span class="field__error"></span></div>
        <div class="field"><label for="{prefix}-phone">Номер телефона <span class="req">*</span></label><input class="input" id="{prefix}-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__" required><span class="field__error" aria-live="polite"></span></div>
        <div class="field field--full"><label for="{prefix}-topic">Что вас интересует</label><select class="select" id="{prefix}-topic" name="topic">{opts}</select></div>
        <div class="field field--full"><label for="{prefix}-comment">Комментарий <span class="muted">(необязательно)</span></label><textarea class="textarea" id="{prefix}-comment" name="comment" placeholder="Вид и возраст питомца, район, удобное время"></textarea></div>
      </div>
      <label class="consent"><input type="checkbox" name="consent" id="{prefix}-consent" value="yes"><span>Согласен(на) на обработку персональных данных по <a href="privacy.html">политике конфиденциальности</a>.</span></label>
      <button class="btn btn--primary btn--block" type="submit">{icon("phone")}Жду звонка</button>
      <div class="form-status" role="status" hidden></div>
    </form>'''


def modals():
    return f'''<dialog class="modal" id="callback-modal" aria-labelledby="cbm-title">
  <div style="position:relative">
    {form_fields("cbm", title='<span id="cbm-title">Оставьте заявку</span>', sub="Перезвоним, спокойно всё обсудим и подберём время визита.", name="modal")}
    <button class="icon-btn modal__close" type="button" data-close aria-label="Закрыть">{icon("close")}</button>
  </div>
</dialog>
<dialog class="modal search-modal" id="search-modal" aria-label="Поиск по сайту">
  <div class="search-box">
    <div class="search-box__field">{icon("search")}<label class="sr-only" for="search-input">Что найти</label><input id="search-input" type="search" placeholder="Например: кремация, цены, кошка" autocomplete="off"><button class="icon-btn" type="button" data-close aria-label="Закрыть поиск">{icon("close")}</button></div>
    <ul class="search-results" id="search-results"></ul>
  </div>
</dialog>'''


# --------------------------------------------------------------------------
# Общие блоки страниц
# --------------------------------------------------------------------------
def cta_section(title="Можно начать с разговора", text="Не нужно заранее знать, какая услуга нужна. Расскажите о ситуации — объясним варианты и порядок визита, без давления и спешки.", eyebrow="Мы на связи"):
    return f'''<section class="section section--tight" id="svyaz">
  <div class="container">
    <div class="cta">
      <div class="cta__text">
        <span class="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p class="lead">{text}</p>
        {phone_link("cta__phone", f'<span class="cta__phone-ico">{icon("phone")}</span><span class="cta__phone-num">{PHONE_TXT}<small>{HOURS_TXT} · {CITY_TXT} {REGION_TXT}</small></span>')}
        <ul class="cta__facts">
          <li>{icon("steth")}<span>Ветеринарные<br>врачи</span></li>
          <li>{icon("clock")}<span>Без спешки<br>и давления</span></li>
          <li>{icon("doc")}<span>Стоимость — до<br>начала работы</span></li>
        </ul>
      </div>
      {form_fields("cta")}
    </div>
  </div>
</section>'''


def calc_section(head=True, id_="kalkulyator"):
    h = f'''<div class="section-head"><div class="section-head__text"><span class="eyebrow">Без телефона и регистрации</span><h2>Рассчитайте стоимость</h2><p class="lead">Ответьте на четыре вопроса — покажем, из чего складывается сумма. Это ориентир, точную стоимость подтвердим до начала работы.</p></div></div>''' if head else ""
    return f'''<section class="section" id="{id_}">
  <div class="container">
    {h}
    <div data-calc><noscript><p class="panel">Калькулятор работает при включённом JavaScript. Цены — в таблице выше, точную сумму назовём по телефону.</p></noscript></div>
  </div>
</section>'''


def prices_panel(title="Цена зависит от вида и веса питомца", sub="Основные услуги в одной таблице. Выезд, урна и доставка считаются отдельно.", mode="all", id_="prajs"):
    return f'''<section class="section" id="{id_}">
  <div class="container">
    <div class="prices-panel">
      <div class="prices-panel__main">
        <div class="section-head__text"><h2>{title} <span class="badge demo-flag">Демо-цены</span></h2><p class="muted">{sub}</p></div>
        <div data-price-table="{mode}"><noscript><p>Для просмотра цен включите JavaScript или позвоните нам.</p></noscript></div>
        <p class="prices-note">Окончательную стоимость врач подтверждает до начала работы. Если на месте понадобится что-то сверх согласованного, сначала спросим вас.</p>
      </div>
      <a class="calc-teaser" href="ceny.html#kalkulyator">
        <span class="calc-teaser__ico">{icon("calc")}</span>
        <strong>Рассчитать стоимость</strong>
        <span>Предварительный расчёт за 4 шага</span>
        <span class="round-arrow">{icon("arrow-right")}</span>
      </a>
    </div>
  </div>
</section>'''


def team_cards(n=4):
    tags = [("home", "Выезд на дом"), ("chat", "Консультации"), ("steth", "Осмотр и сопровождение"), ("heart", "Деликатный подход")]
    silhouette = '<svg viewBox="0 0 120 130" aria-hidden="true"><circle cx="60" cy="46" r="26" fill="currentColor"/><path d="M12 130c0-30 21.5-50 48-50s48 20 48 50z" fill="currentColor"/></svg>'
    cards = ""
    for i in range(n):
        ic, tag = tags[i % len(tags)]
        cards += f'''<article class="doc">
      <div class="doc__photo">{silhouette}<span class="doc__photo-label">{icon("photo")} Фото врача</span></div>
      <div class="doc__body">
        <h3 class="doc__name">Имя Фамилия</h3>
        <span class="doc__role">Ветеринарный врач</span>
        <span class="chip doc__tag">{icon(ic)}{tag}</span>
        <p class="doc__text">Место для короткого рассказа о враче: опыт, специализация, как он работает с владельцами.</p>
      </div>
    </article>'''
    return f'<div class="team">{cards}</div>'


ARTICLES = [
    ("stati-podgotovka.html", "home", "pered", "Перед визитом", "Как подготовиться к визиту ветеринара", "Место, документы, другие животные и дети: что продумать заранее, чтобы прощание было спокойным."),
    ("stati-kremaciya.html", "flame", "kremaciya", "Кремация", "Общая или индивидуальная кремация: как выбрать", "Чем отличаются форматы, что получает владелец и какие вопросы задать перед выбором."),
    ("stati-pitomec-umer.html", "heart", "posle", "Если питомец умер", "Питомец умер дома: что делать в первые часы", "Пошаговая памятка: как подготовить тело, куда звонить и что уточнить перед вывозом."),
    ("stati-poterya.html", "leaf", "posle", "После утраты", "Как пережить уход питомца и поговорить с детьми", "Горе, чувство вины и разговор с ребёнком — что помогает и когда стоит попросить поддержки."),
]


def article_cards(items=None, with_cat=False):
    items = items or ARTICLES[:3]
    out = ""
    for href, ic, cat, label, title, desc in items:
        dc = f' data-cat="{cat}"' if with_cat else ""
        out += f'''<a class="article-card" href="{href}"{dc}>
        <span class="article-card__ico">{icon(ic)}</span>
        <span class="article-card__body"><span class="eyebrow">{label}</span><h3>{title}</h3><p>{desc}</p><span class="link-arrow">Читать{icon("arrow-right")}</span></span>
      </a>'''
    return out


def zone_block(heading="h2"):
    return f'''<div class="zone">
      <div class="zone__text">
        <span class="eyebrow">Территория выезда</span>
        <{heading}>{CITY_TXT} {REGION_TXT}</{heading}>
        <p class="muted">Приезжаем по всему городу и в пригороды. Назовите адрес — оператор скажет, когда врач сможет приехать и нужна ли доплата за выезд.</p>
        <div class="zone__list" data-zone-list></div>
      </div>
      <div class="zone__map">
        <div data-zone-map></div>
        <p class="zone__map-caption">{icon("info")} Схема условная. Точные границы зон уточняйте по телефону.</p>
      </div>
    </div>'''


def faq_item(q, a, id_=None):
    i = f' id="{id_}"' if id_ else ""
    return f'<details class="faq-item"{i}><summary>{q}{icon("chev", "icon chev")}</summary><div class="faq-item__body">{a}</div></details>'


def faq_grid(items):
    half = (len(items) + 1) // 2
    cols = [items[:half], items[half:]]
    return '<div class="faq">' + "".join('<div class="faq__col">' + "".join(faq_item(*x) for x in col) + "</div>" for col in cols) + "</div>"


FAQ = {
    "kogda": ("Как понять, что пора обсудить эвтаназию?", "<p>Чёткой границы нет. Обычно об этом говорят, когда болезнь неизлечима, а боль и другие тяжёлые симптомы не удаётся облегчить лечением: питомец перестаёт есть, с трудом дышит или встаёт, не радуется привычным вещам.</p><p>Врач осмотрит животное и честно расскажет о вариантах. Решение всегда остаётся за вами.</p>"),
    "osmotr": ("Может ли врач сначала просто осмотреть питомца?", "<p>Да. Любой визит начинается с осмотра и разговора. Если врач увидит, что питомцу можно помочь лечением или обезболиванием, он скажет об этом. Процедуру проводят только при медицинских показаниях и только с вашего согласия.</p>"),
    "bol": ("Почувствует ли питомец боль?", "<p>Перед основным этапом животному вводят седативный препарат, и оно засыпает. Следующий этап врач начинает, только когда убедится, что питомец в глубоком сне и ничего не чувствует.</p>"),
    "ryadom": ("Можно ли быть рядом во время процедуры?", "<p>Да. Многие владельцы остаются рядом, гладят питомца и говорят с ним. Если вам слишком тяжело, можно выйти в другую комнату. Время попрощаться будет и до процедуры, и после.</p>"),
    "dlitsya": ("Сколько длится визит врача?", "<p>Обычно от 40 минут до полутора часов. Мы не торопимся: время нужно на осмотр, разговор, ваши вопросы и прощание.</p>"),
    "podgotovka": ("Как подготовиться к приезду врача?", "<p>Выберите тихое место, где питомцу привычно, и постелите пелёнку. Подготовьте выписки из клиники, если они есть. Подумайте, будут ли рядом дети и другие животные.</p><p>Подробнее — в <a href=\"stati-podgotovka.html\">памятке о подготовке к визиту</a>.</p>"),
    "cena": ("Как узнать стоимость заранее?", "<p>Ориентир — в <a href=\"ceny.html#prajs\">прайсе</a> и <a href=\"ceny.html#kalkulyator\">калькуляторе</a>. Точную сумму оператор назовёт по телефону, когда узнает вид и вес питомца, адрес и нужные услуги. Врач подтвердит стоимость до начала работы.</p>"),
    "umer": ("Что делать, если питомец умер дома?", "<p>Позвоните нам: подскажем, что сделать до приезда специалиста, и организуем вывоз на кремацию. Тело лучше положить на пелёнку в прохладном месте и накрыть тканью.</p><p>Пошагово — в <a href=\"stati-pitomec-umer.html\">памятке для владельцев</a>.</p>"),
    "format": ("Чем общая кремация отличается от индивидуальной?", "<p>При общей кремации животных кремируют вместе, прах владельцу не возвращают. При индивидуальной питомца кремируют отдельно и передают вам прах в урне. Для индивидуальной кремации можно заказать фото- и видеоотчёт.</p>"),
    "prah": ("Когда я получу прах?", "<p>Срок зависит от загрузки крематория — точную дату назовём при оформлении. Урну можно забрать самостоятельно или заказать доставку на дом.</p>"),
    "noch": ("Можно ли вызвать врача срочно?", "<p>Позвоните и опишите ситуацию — оператор скажет, через сколько врач сможет приехать по вашему адресу. Время прибытия зависит от района и загрузки врачей.</p>"),
    "dokumenty": ("Какие документы я получу?", "<p>Состав документов зависит от услуги — уточните его у оператора при звонке. Перечень можно заранее согласовать, если документы нужны для клиники, работы или других целей.</p>"),
}


def faq_keys(keys):
    return [(FAQ[k][0], FAQ[k][1], f"faq-{k}") for k in keys]


PARTS = {
    "cta": cta_section(),
    "calc": calc_section(),
    "prices": prices_panel(),
    "prices-cremation": prices_panel(title="Цена кремации зависит от веса", sub="Общая и индивидуальная кремация по видам питомцев. Урна и доставка — отдельно.", mode="cremation"),
    "chev": icon("chev", "icon chev"),
    "team": team_cards(),
    "articles3": article_cards(),
    "articles-all": article_cards(ARTICLES, with_cat=True),
    "zone": zone_block(),
    "zone-h1": zone_block("h1"),
    "faq-home": faq_grid(faq_keys(["kogda", "osmotr", "bol", "ryadom", "dlitsya", "podgotovka", "cena", "umer", "format", "prah"])),
    "faq-usyplenie": faq_grid(faq_keys(["kogda", "osmotr", "bol", "ryadom", "dlitsya", "podgotovka"])),
    "faq-kremaciya": faq_grid(faq_keys(["format", "prah", "umer", "dokumenty"])),
    "faq-ceny": faq_grid(faq_keys(["cena", "noch", "format", "dokumenty"])),
    "faq-zona": faq_grid(faq_keys(["noch", "cena"])),
    "phone": phone_link("", PHONE_TXT),
    "phone-text": PHONE_TXT,
    "hours": HOURS_TXT,
    "city": CITY_TXT,
    "region": REGION_TXT,
    "email": EMAIL_LINK,
    "form-feedback": form_fields("fb", topic_default="Другое", title="Оставить отзыв или вопрос", sub="Напишите, что было хорошо и что стоит улучшить. Мы прочитаем каждое сообщение.", name="feedback"),
    "form-contacts": form_fields("ct"),
    "emblem-big": emblem("big", 120, "emblem-big"),
}


def faq_section_all():
    groups = [
        ("vizit", "Визит врача", ["kogda", "osmotr", "bol", "ryadom", "dlitsya", "podgotovka", "noch"]),
        ("kremaciya", "Кремация и прощание", ["format", "prah", "umer"]),
        ("stoimost", "Стоимость и документы", ["cena", "dokumenty"]),
    ]
    out = ""
    for gid, title, keys in groups:
        out += f'<div class="faq-group" id="{gid}"><h2>{title}</h2><div class="faq faq--single"><div class="faq__col">' + "".join(faq_item(*x) for x in faq_keys(keys)) + "</div></div></div>"
    return out


PARTS["faq-all"] = faq_section_all()


# --------------------------------------------------------------------------
# Сборка
# --------------------------------------------------------------------------
def page(meta, body):
    title = meta["title"]
    desc = meta["description"]
    noindex = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
{noindex}
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{SITE_URL}assets/img/og-image.png">
<meta name="theme-color" content="#2866a0">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=Lora:ital,wght@1,500&display=swap">
<link rel="stylesheet" href="assets/css/style.css?v={VER}">
</head>
<body>
{SPRITE}
{header(meta.get("nav", ""))}
<main id="main">
{body}
</main>
{footer()}
{modals()}
<script src="assets/js/config.js?v={VER}"></script>
<script src="assets/js/main.js?v={VER}"></script>
</body>
</html>
'''


def render(text):
    text = re.sub(r"\{\{i:([a-z0-9-]+)\}\}", lambda m: icon(m.group(1)), text)
    text = re.sub(r"\{\{part:([a-z0-9-]+)\}\}", lambda m: PARTS[m.group(1)], text)
    return text


def main():
    pages = sorted((SRC / "pages").glob("*.html"))
    for p in pages:
        raw = p.read_text(encoding="utf-8")
        first, _, body = raw.partition("\n")
        meta = json.loads(first)
        html = page(meta, render(body))
        out = OUT / meta.get("out", p.name)
        out.write_text(html, encoding="utf-8")
        print("✓", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
