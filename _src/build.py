#!/usr/bin/env python3
"""Сборка статического сайта «Мягкий Свет».

Данные компании — в _src/site.json (единственный источник: NAP, цены, зоны,
мессенджеры, аналитика). Пустое значение = данных нет: на сайте выводится
метка [ADD REAL ...], в Schema.org поле не попадает.

Страницы — _src/pages/*.html. Первая строка страницы — JSON с метаданными:
  title, description, nav, crumbs [[подпись, ссылка], ...], type (WebPage/AboutPage/...),
  service {name, serviceType, description, priceKeys}, article {headline, datePublished}.

Шорткоды:
  {{i:name}}            иконка
  {{part:name}}         общий блок (PARTS)
  {{d:key}}             данные компании (phone, hours, city, area, email, experience, duration, legal, address)
  {{price:key}}         «от N ₽» по услуге/доп. услуге или метка [ADD REAL PRICE]
  {{prices:mode:group}} таблица цен (mode: all|euth|cremation; group: all|cat|dog|other)
  {{faq:k1,k2,...}}     блок вопросов (попадает и в FAQPage-разметку)
  {{cta:текст}}         полоса с призывом к действию
  {{crumbs}}            хлебные крошки (+ BreadcrumbList)
  {{cityIn}}            « в Казани» или пусто

Запуск: python3 _src/build.py  → site/
"""
import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icons import ICONS, SPRITE, emblem, icon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
OUT = ROOT / "site"
D = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
VER = time.strftime("%Y%m%d%H%M%S")
TODAY = date.today().isoformat()

BRAND = D["brand"]
TAGLINE = D["tagline"]
SITE_URL = D["siteUrl"].rstrip("/") + "/"
BASE_PATH = "/" + SITE_URL.split("://", 1)[1].split("/", 1)[1] if "/" in SITE_URL.split("://", 1)[1] else "/"
ORG_ID = SITE_URL + "#org"
WEBSITE_ID = SITE_URL + "#website"
NBSP = " "


# --------------------------------------------------------------------------
# Данные и метки-заглушки
# --------------------------------------------------------------------------
def tok(name):
    return f'<span class="tk" title="Данные не заполнены: укажите в _src/site.json">[ADD REAL {name}]</span>'


def has(v):
    return bool(v) and (not isinstance(v, (list, dict)) or any(has(x) for x in (v.values() if isinstance(v, dict) else v)))


def rub(n):
    return f"{n:,}".replace(",", NBSP) + NBSP + "₽"


def digits(s):
    return re.sub(r"\D", "", s or "")


PHONE_HREF = ("+" + digits(D["phone"])) if digits(D["phone"]) else ""
WA_URL = f"https://wa.me/{digits(D['whatsapp'])}" if digits(D["whatsapp"]) else ""
TG_URL = f"https://t.me/{D['telegram'].lstrip('@')}" if D["telegram"] else ""
CITY_IN = (" " + D["cityIn"].strip()) if D["cityIn"].strip() else ""


def address_text():
    a = D["address"]
    parts = [a.get("postalCode"), a.get("region"), a.get("locality"), a.get("street")]
    return ", ".join(p for p in parts if p)


def legal_text():
    l = D["legal"]
    parts = [l.get("name"), f"ИНН {l['inn']}" if l.get("inn") else "", f"ОГРН {l['ogrn']}" if l.get("ogrn") else "", l.get("license")]
    return ", ".join(p for p in parts if p)


def dval(key):
    """HTML-значение данных компании или метка."""
    if key == "phone":
        return f'<a href="tel:{PHONE_HREF}" class="nowrap">{html.escape(D["phone"])}</a>' if PHONE_HREF else tok("PHONE")
    if key == "phone-text":
        return html.escape(D["phone"]) if PHONE_HREF else tok("PHONE")
    if key == "email":
        return f'<a href="mailto:{html.escape(D["email"])}">{html.escape(D["email"])}</a>' if D["email"] else tok("EMAIL")
    if key == "hours":
        return html.escape(D["hours"]) if D["hours"] else tok("HOURS")
    if key == "city":
        return html.escape(D["city"]) if D["city"] else tok("CITY")
    if key == "area":
        return html.escape(D["serviceArea"]) if D["serviceArea"] else tok("SERVICE AREA")
    if key == "experience":
        return html.escape(D["experience"]) if D["experience"] else tok("EXPERIENCE")
    if key == "duration":
        return html.escape(D["visitDuration"]) if D["visitDuration"] else tok("DURATION")
    if key == "address":
        return html.escape(address_text()) if address_text() else tok("ADDRESS")
    if key == "messengers":
        return messenger_links() or tok("WHATSAPP / TELEGRAM")
    if key == "legal":
        return html.escape(legal_text()) if legal_text() else tok("LEGAL INFO")
    raise KeyError(key)


def min_price(key):
    if key in D["services"]:
        vals = [v for v in D["services"][key]["prices"].values() if isinstance(v, (int, float))]
        return min(vals) if vals else None
    if key in D["extras"]:
        v = D["extras"][key]["price"]
        return v if isinstance(v, (int, float)) else None
    raise KeyError(key)


def price_from(key):
    v = min_price(key)
    if v is None:
        return tok("PRICE")
    return ("от " if key in D["services"] else "") + rub(v)


def price_cell(v):
    return rub(v) if isinstance(v, (int, float)) else tok("PRICE")


# --------------------------------------------------------------------------
# Контакты: телефон, мессенджеры
# --------------------------------------------------------------------------
def messenger_links(cls="chip"):
    out = []
    if WA_URL:
        out.append(f'<a class="{cls} msg-wa" href="{WA_URL}" target="_blank" rel="noopener" data-track="whatsapp_click">{icon("whatsapp")}WhatsApp</a>')
    if TG_URL:
        out.append(f'<a class="{cls} msg-tg" href="{TG_URL}" target="_blank" rel="noopener" data-track="telegram_click">{icon("telegram")}Telegram</a>')
    return "".join(out)


def phone_block_header():
    inner = f'<span class="topbar__phone-ico">{icon("phone")}</span><span class="topbar__phone-num">{dval("phone-text")}<small>{dval("hours")}</small></span>'
    if PHONE_HREF:
        return f'<a class="topbar__phone" href="tel:{PHONE_HREF}">{inner}</a>'
    return f'<a class="topbar__phone" href="kontakty.html">{inner}</a>'


# --------------------------------------------------------------------------
# Навигация
# --------------------------------------------------------------------------
NAV = [
    {"id": "usyplenie", "label": "Усыпление", "href": "usyplenie.html",
     "cols": [("По видам питомцев", [("cat", "Кошки и коты", "usyplenie-koshek.html"), ("dog", "Собаки", "usyplenie-sobak.html"), ("rodent", "Грызуны, кролики, хорьки", "usyplenie.html#gryzuny"), ("bird", "Птицы и экзотика", "usyplenie.html#pticy")]),
              ("Перед визитом", [("info", "Когда обсуждают эвтаназию", "usyplenie.html#kogda"), ("steth", "Как проходит визит врача", "usyplenie.html#vizit"), ("home", "Как подготовиться", "usyplenie.html#podgotovka"), ("book", "Памятка: подготовка к визиту", "stati-podgotovka.html")])],
     "promo": ("Стоимость усыпления", "Цена зависит от вида и веса питомца. Посмотрите прайс или соберите расчёт в калькуляторе.", [("ceny.html#prajs", "Смотреть цены"), ("ceny.html#kalkulyator", "Калькулятор")])},
    {"id": "kremaciya", "label": "Кремация", "href": "kremaciya.html",
     "cols": [("Форматы", [("urn", "Индивидуальная кремация", "kremaciya.html#individualnaya"), ("flame", "Общая кремация", "kremaciya.html#obshchaya"), ("doc", "Сравнение форматов", "kremaciya.html#sravnenie")]),
              ("Сопутствующие услуги", [("truck", "Вывоз тела животного", "vyvoz.html"), ("urn", "Урны для праха", "kremaciya.html#urny"), ("route", "Доставка урны", "kremaciya.html#urny"), ("camera", "Фото- и видеоотчёт", "kremaciya.html#otchet")])],
     "promo": ("Питомец умер дома?", "Что сделать в первые часы и как организовать вывоз на кремацию.", [("vyvoz.html", "Вывоз тела"), ("stati-pitomec-umer.html", "Памятка")])},
    {"id": "ceny", "label": "Цены", "href": "ceny.html",
     "cols": [("Стоимость", [("doc", "Прайс по видам и весу", "ceny.html#prajs"), ("info", "Что оплачивается отдельно", "ceny.html#otdelno"), ("calc", "Калькулятор стоимости", "ceny.html#kalkulyator"), ("chat", "Вопросы о ценах", "ceny.html#voprosy")])],
     "promo": ("Точная сумма — до начала работы", "Оператор назовёт стоимость по телефону, врач подтвердит её на месте до процедуры.", [("kontakty.html", "Связаться")])},
    {"id": "o-nas", "label": "О службе", "href": "o-nas.html",
     "cols": [("Служба", [("heart", "Коротко о нас", "o-nas.html#fakty"), ("steth", "Врачи", "o-nas.html#vrachi"), ("shield", "Как мы работаем", "o-nas.html#rabota"), ("map", "Зона выезда", "zona.html")]),
              ("Связь", [("star", "Отзывы", "otzyvy.html"), ("phone", "Контакты", "kontakty.html"), ("lock", "Конфиденциальность", "privacy.html")])],
     "promo": None},
    {"id": "zona", "label": "Зона выезда", "href": "zona.html"},
    {"id": "stati", "label": "Полезное", "href": "stati.html",
     "cols": [("Памятки владельцу", [("home", "Как подготовиться к визиту врача", "stati-podgotovka.html"), ("flame", "Общая или индивидуальная кремация", "stati-kremaciya.html"), ("heart", "Питомец умер дома: что делать", "stati-pitomec-umer.html"), ("leaf", "Как пережить уход питомца", "stati-poterya.html")]),
              ("Справка", [("book", "Все материалы", "stati.html"), ("chat", "Вопросы и ответы", "faq.html")])],
     "promo": None},
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
            cols += f'<div class="mega__col"><p class="mega__title">{title}</p><ul>{lis}</ul></div>'
        if n.get("promo"):
            t, p, links = n["promo"]
            btns = "".join(f'<a class="link-arrow" href="{h}">{l}{icon("arrow-right")}</a>' for h, l in links)
            cols += f'<div class="mega__promo"><strong>{t}</strong><p>{p}</p>{btns}</div>'
        else:
            cols += f'<div class="mega__col"><p class="mega__title">Раздел</p><ul><li><a href="{n["href"]}">{icon("arrow-right")}Весь раздел «{n["label"]}»</a></li></ul></div>'
        items.append(
            f'<li class="nav__item has-mega{cur}"><button class="nav__link" type="button" aria-expanded="false" aria-controls="mega-{n["id"]}">{n["label"]}{icon("chev", "icon chev")}</button>'
            f'<div class="mega" id="mega-{n["id"]}"><div class="container mega__inner" style="--cols:{len(n["cols"]) + 1}">{cols}</div></div></li>'
        )
    return "".join(items)


def mobile_nav():
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


def brand(uid, href="index.html"):
    return f'<a class="brand" href="{href}" aria-label="{BRAND} — на главную">{emblem(uid)}<span class="brand__text"><span class="brand__name">{BRAND}</span><span class="brand__tag">{TAGLINE}</span></span></a>'


def header(active):
    call_mobile = (f'<a class="btn btn--primary btn--block" href="tel:{PHONE_HREF}">{icon("phone")}Позвонить: {html.escape(D["phone"])}</a>' if PHONE_HREF
                   else f'<button class="btn btn--primary btn--block" type="button" data-open="callback" data-topic="Консультация">{icon("chat")}Оставить заявку</button>')
    return f'''<a class="skip-link" href="#main">Перейти к содержимому</a>
<header class="site-header">
  <div class="container topbar">
    {brand("h")}
    <div class="topbar__region">{icon("pin")}<span><strong>{dval("city")}</strong>{dval("area")}</span></div>
    <span class="topbar__spacer"></span>
    {phone_block_header()}
    <button class="btn btn--primary btn--sm topbar__cta" type="button" data-open="callback" data-topic="Усыпление на дому">{icon("chat")}Вызвать врача</button>
    <button class="icon-btn icon-btn--primary topbar__chat" type="button" data-open="callback" data-topic="Усыпление на дому" aria-label="Оставить заявку">{icon("chat")}</button>
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
  <nav aria-label="Мобильное меню"><ul class="m-nav">{mobile_nav()}
    <li><button class="m-nav__link" type="button" data-open="search">Поиск по сайту{icon("search")}</button></li></ul></nav>
  <div class="mobile-menu__contacts">
    {call_mobile}
    <div class="chip-row">{messenger_links()}</div>
    <p class="small muted">{icon("clock")} {dval("hours")} · {dval("area")}</p>
  </div>
</div>'''


FOOTER_COLS = [
    ("Услуги", [("Усыпление на дому", "usyplenie.html"), ("Усыпление кошек", "usyplenie-koshek.html"), ("Усыпление собак", "usyplenie-sobak.html"), ("Кремация животных", "kremaciya.html"), ("Вывоз тела", "vyvoz.html"), ("Урны для праха", "kremaciya.html#urny")]),
    ("Служба", [("О службе", "o-nas.html"), ("Врачи", "o-nas.html#vrachi"), ("Цены", "ceny.html"), ("Калькулятор", "ceny.html#kalkulyator"), ("Зона выезда", "zona.html"), ("Отзывы", "otzyvy.html")]),
    ("Информация", [("Полезное", "stati.html"), ("Вопросы и ответы", "faq.html"), ("Контакты", "kontakty.html"), ("Конфиденциальность", "privacy.html")]),
]


def footer():
    cols = "".join(
        f'<div><p class="footer__title">{t}</p><ul>' + "".join(f'<li><a href="{h}">{l}</a></li>' for l, h in links) + "</ul></div>"
        for t, links in FOOTER_COLS
    )
    fab = ""
    if WA_URL:
        fab = f'<a class="fab fab--wa" href="{WA_URL}" target="_blank" rel="noopener" data-track="whatsapp_click" aria-label="Написать в WhatsApp">{icon("whatsapp")}<span>WhatsApp</span></a>'
    elif TG_URL:
        fab = f'<a class="fab fab--tg" href="{TG_URL}" target="_blank" rel="noopener" data-track="telegram_click" aria-label="Написать в Telegram">{icon("telegram")}<span>Telegram</span></a>'
    else:
        fab = f'<button class="fab" type="button" data-open="callback" data-topic="Консультация">{icon("chat")}<span>Написать нам</span></button>'
    cb1 = (f'<a class="btn btn--primary" href="tel:{PHONE_HREF}">{icon("phone")}<span>Позвонить</span></a>' if PHONE_HREF
           else f'<button class="btn btn--primary" type="button" data-open="callback" data-topic="Консультация">{icon("chat")}<span>Оставить заявку</span></button>')
    if WA_URL:
        cb2 = f'<a class="btn btn--wa" href="{WA_URL}" target="_blank" rel="noopener" data-track="whatsapp_click">{icon("whatsapp")}<span>WhatsApp</span></a>'
    elif TG_URL:
        cb2 = f'<a class="btn btn--tg" href="{TG_URL}" target="_blank" rel="noopener" data-track="telegram_click">{icon("telegram")}<span>Telegram</span></a>'
    elif PHONE_HREF:
        cb2 = f'<button class="btn" type="button" data-open="callback" data-topic="Консультация">{icon("chat")}<span>Заявка</span></button>'
    else:
        cb2 = ""
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer__top">
      <div class="footer__about">
        {brand("f")}
        <p>Выездная ветеринарная помощь: гуманное усыпление на дому, кремация, вывоз тела, урны и доставка праха.</p>
      </div>
      <nav class="footer__nav" aria-label="Меню в подвале">{cols}</nav>
      <div class="footer__contacts">
        <span class="footer__phone">{dval("phone")}</span>
        <span>{dval("hours")}</span>
        <span>{dval("email")}</span>
        <span>{icon("pin")} {dval("area")}</span>
        <div class="chip-row">{messenger_links()}</div>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© <span data-year>{date.today().year}</span> {BRAND}. {TAGLINE}.</span>
      <span><a href="privacy.html">Политика конфиденциальности</a></span>
      <span class="footer__motto">Рядом, когда это важнее всего</span>
    </div>
    <p class="footer__legal">{dval("legal")}. Информация на сайте носит справочный характер и не является публичной офертой. Стоимость услуг подтверждается до начала их оказания.</p>
  </div>
</footer>
{fab}
<div class="callbar">{cb1}{cb2}</div>
<button class="to-top" type="button" aria-label="Наверх">{icon("arrow-up")}</button>'''


# --------------------------------------------------------------------------
# Формы
# --------------------------------------------------------------------------
SERVICES_SELECT = ["Консультация", "Усыпление на дому", "Вывоз тела", "Индивидуальная кремация", "Общая кремация", "Узнать цену", "Другое"]
TIMES = ["Как можно скорее", "Сегодня", "Завтра", "Другое время — обсудим по телефону"]


def form_fields(prefix, topic_default="Консультация", title="Оставить заявку", sub="Перезвоним, ответим на вопросы и согласуем время визита.", name="callback", title_id="", tag="h3"):
    opts = "".join(f'<option{" selected" if t == topic_default else ""}>{t}</option>' for t in SERVICES_SELECT)
    times = "".join(f"<option>{t}</option>" for t in TIMES)
    tid = f' id="{title_id}"' if title_id else ""
    return f'''<form class="form-card" data-form="{name}" novalidate>
      <{tag} class="form-card__title"{tid}>{title}</{tag}>
      <p>{sub}</p>
      <div class="form-grid">
        <div class="field"><label for="{prefix}-name">Имя</label><input class="input" id="{prefix}-name" name="name" type="text" autocomplete="name" placeholder="Как к вам обращаться"><span class="field__error"></span></div>
        <div class="field"><label for="{prefix}-phone">Телефон или WhatsApp <span class="req">*</span></label><input class="input" id="{prefix}-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__" required><span class="field__error" aria-live="polite"></span></div>
        <div class="field"><label for="{prefix}-topic">Услуга</label><select class="select" id="{prefix}-topic" name="topic">{opts}</select></div>
        <div class="field"><label for="{prefix}-time">Удобное время</label><select class="select" id="{prefix}-time" name="time">{times}</select></div>
        <div class="field field--full"><label for="{prefix}-location">Район или адрес</label><input class="input" id="{prefix}-location" name="location" type="text" autocomplete="street-address" placeholder="Например: район и улица"></div>
      </div>
      <input type="hidden" name="details" value="">
      <p class="form-details" hidden></p>
      <label class="consent"><input type="checkbox" name="consent" id="{prefix}-consent" value="yes"><span>Согласен(на) на обработку персональных данных по <a href="privacy.html">политике конфиденциальности</a>.</span></label>
      <button class="btn btn--primary btn--block" type="submit">{icon("send")}Отправить заявку</button>
      <div class="form-status" role="status" hidden></div>
    </form>'''


def modals():
    return f'''<dialog class="modal" id="callback-modal" aria-labelledby="cbm-title">
  <div style="position:relative">
    {form_fields("cbm", title="Оставьте заявку", sub="Перезвоним, спокойно всё обсудим и подберём время визита.", name="modal", title_id="cbm-title", tag="h2")}
    <button class="icon-btn modal__close" type="button" data-close aria-label="Закрыть">{icon("close")}</button>
  </div>
</dialog>
<dialog class="modal search-modal" id="search-modal" aria-label="Поиск по сайту">
  <div class="search-box">
    <div class="search-box__field">{icon("search")}<label class="sr-only" for="search-input">Что найти</label><input id="search-input" type="search" placeholder="Например: кремация, цены, кошка" autocomplete="off"><button class="icon-btn" type="button" data-close aria-label="Закрыть поиск">{icon("close")}</button></div>
    <ul class="search-results" id="search-results"></ul>
  </div>
</dialog>
<div class="cookie" id="cookie" hidden>
  <p>Сайт использует cookie и системы веб-аналитики, чтобы понимать, какие страницы полезны. Подробнее — в <a href="privacy.html">политике конфиденциальности</a>.</p>
  <div class="btn-row"><button class="btn btn--primary btn--sm" type="button" data-consent="yes">Принять</button><button class="btn btn--sm" type="button" data-consent="no">Отказаться</button></div>
</div>'''


# --------------------------------------------------------------------------
# Общие блоки
# --------------------------------------------------------------------------
def contact_buttons():
    out = [f'<button class="btn btn--primary" type="button" data-open="callback" data-topic="Усыпление на дому">{icon("chat")}Оставить заявку</button>']
    if PHONE_HREF:
        out.append(f'<a class="btn" href="tel:{PHONE_HREF}">{icon("phone")}Позвонить</a>')
    if WA_URL:
        out.append(f'<a class="btn btn--wa" href="{WA_URL}" target="_blank" rel="noopener" data-track="whatsapp_click">{icon("whatsapp")}WhatsApp</a>')
    if TG_URL:
        out.append(f'<a class="btn btn--tg" href="{TG_URL}" target="_blank" rel="noopener" data-track="telegram_click">{icon("telegram")}Telegram</a>')
    return "".join(out)


def cta_strip(text):
    return f'<div class="cta-strip"><p>{text}</p><div class="btn-row">{contact_buttons()}</div></div>'


def cta_section(title="Можно начать с разговора", text="Не нужно заранее знать, какая услуга нужна. Расскажите о ситуации — объясним варианты и порядок визита, без давления и спешки."):
    phone_inner = f'<span class="cta__phone-ico">{icon("phone")}</span><span class="cta__phone-num">{dval("phone-text")}<small>{dval("hours")}</small></span>'
    phone = f'<a class="cta__phone" href="tel:{PHONE_HREF}">{phone_inner}</a>' if PHONE_HREF else f'<div class="cta__phone">{phone_inner}</div>'
    return f'''<section class="section section--tight" id="svyaz">
  <div class="container">
    <div class="cta">
      <div class="cta__text">
        <span class="eyebrow">Мы на связи</span>
        <h2>{title}</h2>
        <p class="lead">{text}</p>
        {phone}
        <div class="chip-row">{messenger_links()}</div>
        <ul class="cta__facts">
          <li>{icon("pin")}<span>Зона выезда:<br>{dval("area")}</span></li>
          <li>{icon("doc")}<span>Стоимость — до<br>начала работы</span></li>
        </ul>
      </div>
      {form_fields("cta")}
    </div>
  </div>
</section>'''


def calc_section():
    return f'''<section class="section" id="kalkulyator">
  <div class="container">
    <div class="section-head"><div class="section-head__text"><span class="eyebrow">Без телефона и регистрации</span><h2>Быстрый расчёт и запрос цены</h2><p class="lead">Ответьте на четыре вопроса — покажем, из чего складывается стоимость, и отправим расчёт нам одним нажатием.</p></div></div>
    <div class="calc-mount" data-calc><noscript><p class="panel">Калькулятор работает при включённом JavaScript. Цены — в таблице на этой странице, точную сумму назовём по телефону.</p></noscript></div>
  </div>
</section>'''


TAB_GROUPS = [("cat", "Кошки", "cat", ["cat"]), ("dog", "Собаки", "dog", ["dog"]), ("other", "Другие животные", "paw", ["small", "bird", "exotic"])]
_tab_counter = [0]


def price_tables(mode="all", group="all"):
    cols = {"euth": ["euth"], "cremation": ["common", "individual"]}.get(mode, ["euth", "common", "individual"])
    groups = [g for g in TAB_GROUPS if group == "all" or g[0] == group]
    _tab_counter[0] += 1
    uid = f"pt{_tab_counter[0]}"
    out = ""
    if len(groups) > 1:
        out += '<div class="tabs" role="tablist" aria-label="Вид питомца">' + "".join(
            f'<button class="tab" role="tab" type="button" id="{uid}-t{i}" aria-controls="{uid}-p{i}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{icon(ic)}{label}</button>'
            for i, (_, label, ic, _sp) in enumerate(groups)) + "</div>"
    for i, (gid, label, ic, sp_ids) in enumerate(groups):
        rows = ""
        for sid in sp_ids:
            sp = D["species"][sid]
            for wid in sp["weights"]:
                w = next(x for x in D["weights"] if x["id"] == wid)
                name = w["label"] if len(sp_ids) == 1 else sp["label"] + (", " + w["label"] if len(sp["weights"]) > 1 else "")
                rows += f'<tr><th scope="row">{html.escape(name)}</th>' + "".join(f"<td>{price_cell(D['services'][c]['prices'][wid])}</td>" for c in cols) + "</tr>"
        if mode != "euth":
            rows += f'<tr class="row-sep"><th scope="row">{D["extras"]["pickup"]["label"]}</th><td colspan="{len(cols)}">{price_cell(D["extras"]["pickup"]["price"])}</td></tr>'
        rows += f'<tr><th scope="row">Выезд за город</th><td colspan="{len(cols)}">доплата по зоне · <a href="zona.html">зоны выезда</a></td></tr>'
        head = "".join(f'<th scope="col">{D["services"][c]["label"]}<br><small>{D["services"][c]["note"]}</small></th>' for c in cols)
        role = f' role="tabpanel" id="{uid}-p{i}" aria-labelledby="{uid}-t{i}"' if len(groups) > 1 else ""
        hidden = " hidden" if i > 0 else ""
        caption = f'<caption class="sr-only">Цены: {label.lower()}</caption>'
        out += f'<div class="table-wrap"{role}{hidden}><table class="price-table">{caption}<thead><tr><th scope="col">{"Вес питомца" if len(sp_ids) == 1 else "Питомец"}</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    return f'<div class="price-tables" data-price-tabs>{out}</div>'


def prices_panel(title="Цена зависит от вида и веса питомца", sub="Основные услуги в одной таблице. Выезд за город, урна и доставка считаются отдельно.", mode="all", group="all", id_="prajs"):
    return f'''<section class="section" id="{id_}">
  <div class="container">
    <div class="prices-panel">
      <div class="prices-panel__main">
        <div class="section-head__text"><h2>{title}</h2><p class="muted">{sub}</p></div>
        {price_tables(mode, group)}
        <p class="prices-note">Окончательную стоимость врач подтверждает до начала работы. Если на месте понадобится что-то сверх согласованного, сначала спросим вас.</p>
      </div>
      <a class="calc-teaser" href="ceny.html#kalkulyator">
        <span class="calc-teaser__ico">{icon("calc")}</span>
        <strong>Узнать точную цену</strong>
        <span>Расчёт за 4 шага и запрос стоимости</span>
        <span class="round-arrow">{icon("arrow-right")}</span>
      </a>
    </div>
  </div>
</section>'''


def team_cards(n=4):
    silhouette = '<svg viewBox="0 0 120 130" aria-hidden="true"><circle cx="60" cy="46" r="26" fill="currentColor"/><path d="M12 130c0-30 21.5-50 48-50s48 20 48 50z" fill="currentColor"/></svg>'
    card = f'''<article class="doc">
      <div class="doc__photo">{silhouette}<span class="doc__photo-label">[ADD REAL PHOTO]</span></div>
      <div class="doc__body">
        <h3 class="doc__name">{tok("NAME")}</h3>
        <span class="doc__role">Ветеринарный врач</span>
        <p class="doc__text">Образование, стаж, специализация: {tok("EXPERIENCE")}</p>
      </div>
    </article>'''
    return '<div class="team">' + card * n + "</div>"


ARTICLES = [
    ("stati-podgotovka.html", "home", "pered", "Перед визитом", "Как подготовиться к визиту ветеринара", "Место, документы, другие животные и дети: что продумать заранее, чтобы прощание было спокойным."),
    ("stati-kremaciya.html", "flame", "kremaciya", "Кремация", "Общая или индивидуальная кремация: как выбрать", "Чем отличаются форматы, что получает владелец и какие вопросы задать перед выбором."),
    ("stati-pitomec-umer.html", "heart", "posle", "Если питомец умер", "Питомец умер дома: что делать в первые часы", "Пошаговая памятка: как подготовить тело, куда звонить и что уточнить перед вывозом."),
    ("stati-poterya.html", "leaf", "posle", "После утраты", "Как пережить уход питомца и поговорить с детьми", "Горе, чувство вины и разговор с ребёнком — что помогает и когда стоит попросить поддержки."),
]


def article_cards(items=None, with_cat=False):
    out = ""
    for href, ic, cat, label, title, desc in items or ARTICLES[:3]:
        dc = f' data-cat="{cat}"' if with_cat else ""
        out += f'''<a class="article-card" href="{href}"{dc}>
        <span class="article-card__ico">{icon(ic)}</span>
        <span class="article-card__body"><span class="eyebrow">{label}</span><span class="article-card__title">{title}</span><span class="article-card__desc">{desc}</span><span class="link-arrow">Читать{icon("arrow-right")}</span></span>
      </a>'''
    return out


def zone_map_svg():
    zones = list(reversed(D["zones"]))
    radii = [140, 100, 60, 40]
    rings, labels = "", ""
    for i, z in enumerate(zones):
        r = radii[i] if i < len(radii) else 30
        rings += f'<circle cx="200" cy="155" r="{r}" fill="{z["color"]}" fill-opacity="0.28" stroke="{z["color"]}" stroke-width="1.5"/>'
        if i < len(zones) - 1:
            labels += f'<text x="200" y="{155 - r + 18}" text-anchor="middle" font-size="11" font-weight="600" fill="#56718a">{html.escape(z["label"])}</text>'
    city = html.escape(D["city"]) if D["city"] else "Город"
    return (f'<svg viewBox="0 0 400 310" role="img" aria-label="Схема зон выезда от центра города к пригородам">'
            f'<g stroke="#e0edf5" stroke-width="2" fill="none"><path d="M20 230 C 120 190, 160 170, 200 155 S 320 90, 390 60"/><path d="M60 30 C 120 90, 170 130, 200 155 S 260 250, 300 300"/><path d="M0 155 H400"/></g>'
            f'{rings}{labels}<g transform="translate(200 147)"><circle r="15" fill="#fff"/><path d="M0 9s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" fill="#2866a0"/><circle cy="-2" r="2.6" fill="#fff"/></g>'
            f'<text x="200" y="182" text-anchor="middle" font-size="11.5" font-weight="700" fill="#143b5b" stroke="#fff" stroke-width="3" paint-order="stroke">{city}</text></svg>')


def zone_block(heading="h2"):
    rows = ""
    for z in D["zones"]:
        note = html.escape(z["note"]) if z["note"] else tok("SERVICE AREA")
        price = ("без доплаты" if z["price"] == 0 else "доплата " + rub(z["price"])) if isinstance(z["price"], (int, float)) else "доплата: " + tok("PRICE")
        rows += f'<div class="zone__row"><span class="zone__row-name"><span class="zone__dot" style="background:{z["color"]}"></span>{html.escape(z["label"])}</span><span class="zone__row-note">{note}<br>{price}</span></div>'
    return f'''<div class="zone">
      <div class="zone__text">
        <span class="eyebrow">Территория выезда</span>
        <{heading}>Зона выезда: {dval("city")}</{heading}>
        <p class="muted">Где работаем: {dval("area")}. Назовите адрес — оператор скажет, когда врач сможет приехать и нужна ли доплата за выезд.</p>
        <div class="zone__list">{rows}</div>
      </div>
      <div class="zone__map">
        {zone_map_svg()}
        <p class="zone__map-caption">{icon("info")} Схема условная. Точные границы зон уточняйте по телефону.</p>
      </div>
    </div>'''


def facts_block(heading="h2"):
    """Блок «Коротко о службе»: ясные факты для людей и AI-систем."""
    contacts = []
    contacts.append(f"телефон {dval('phone')}")
    if WA_URL:
        contacts.append(f'<a href="{WA_URL}" data-track="whatsapp_click" target="_blank" rel="noopener">WhatsApp</a>')
    if TG_URL:
        contacts.append(f'<a href="{TG_URL}" data-track="telegram_click" target="_blank" rel="noopener">Telegram</a>')
    contacts.append('<a href="kontakty.html">форма заявки</a>')
    rows = [
        ("Кто мы", f"«{BRAND}» — выездная ветеринарная служба. Врачи приезжают к питомцу домой."),
        ("Услуги", 'Гуманное <a href="usyplenie.html">усыпление животных на дому</a> по медицинским показаниям, <a href="kremaciya.html">общая и индивидуальная кремация</a>, <a href="vyvoz.html">вывоз тела</a>, урны и доставка праха.'),
        ("Для кого", "Владельцы кошек, собак, грызунов, кроликов, хорьков, птиц и рептилий."),
        ("Где работаем", dval("area")),
        ("Часы работы", dval("hours")),
        ("Цены", f'Усыпление на дому — {price_from("euth")}, общая кремация — {price_from("common")}, индивидуальная — {price_from("individual")}. <a href="ceny.html">Полный прайс</a>.'),
        ("Опыт", dval("experience")),
        ("Как связаться", ", ".join(contacts) + "."),
    ]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    return f'''<div class="facts">
      <{heading} class="facts__title">Коротко о службе</{heading}>
      <dl class="facts__list">{dl}</dl>
    </div>'''


def districts_block():
    def chips(lst, name):
        if not lst:
            return f'<p>{tok(name)}</p>'
        return '<div class="chip-row">' + "".join(f'<span class="chip">{icon("pin")}{html.escape(x)}</span>' for x in lst) + "</div>"
    return (f'<div class="grid grid-2"><div class="panel"><h3>Город: {dval("city")}</h3>{chips(D["districts"]["city"], "DISTRICTS")}</div>'
            f'<div class="panel"><h3>Пригороды</h3>{chips(D["districts"]["suburbs"], "SUBURBS")}</div></div>')


def review_cards(n=3):
    card = f'''<article class="review"><div class="review__head"><span class="review__avatar">{icon("user")}</span><span class="review__who"><strong>{tok("NAME")}</strong><small>Отзыв владельца</small></span></div><p class="review__text">{tok("REVIEW")}</p><span class="review__tag">{icon("check")}Публикуется с согласия автора</span></article>'''
    return card * n


def review_links():
    names = {"yandex": "Яндекс Картах", "google": "Google Картах", "twogis": "2ГИС"}
    links = [f'<a class="btn" href="{html.escape(u)}" target="_blank" rel="noopener">{icon("star")}Отзыв на {names[k]}</a>' for k, u in D["reviewLinks"].items() if u]
    if not links:
        return f'<p class="muted small">Ссылки на карточки в Яндекс Картах, Google Картах и 2ГИС: {tok("REVIEW LINKS")}</p>'
    return '<div class="btn-row">' + "".join(links) + "</div>"


# --------------------------------------------------------------------------
# Вопросы и ответы
# --------------------------------------------------------------------------
FAQ = {
    "vkljuchaet": ("Что входит в усыпление на дому?", "<p>Осмотр питомца и разговор с вами, седация (животное засыпает), основной этап процедуры, подтверждение врачом остановки сердца и время на прощание. Вывоз тела и кремация — отдельные услуги, их можно заказать вместе с визитом.</p>"),
    "cena": (f"Сколько стоит усыпление на дому{CITY_IN}?", f"<p>Цена зависит от вида и веса питомца: усыпление на дому — {price_from('euth')}. Выезд за пределы города, кремация, урна и доставка считаются отдельно. Полный прайс — на странице <a href=\"ceny.html\">«Цены»</a>, точную сумму оператор назовёт по телефону до выезда.</p>"),
    "kogda": ("Как понять, что пора обсудить эвтаназию?", "<p>Чёткой границы нет. Обычно об этом говорят, когда болезнь неизлечима, а боль и другие тяжёлые симптомы не удаётся облегчить лечением: питомец перестаёт есть, с трудом дышит или встаёт, не радуется привычным вещам.</p><p>Врач осмотрит животное и честно расскажет о вариантах. Решение всегда остаётся за вами.</p>"),
    "osmotr": ("Может ли врач сначала просто осмотреть питомца?", "<p>Да. Визит начинается с осмотра и разговора. Если врач увидит, что питомцу можно помочь лечением или обезболиванием, он скажет об этом. Процедуру проводят только при медицинских показаниях и только с вашего согласия.</p>"),
    "bol": ("Почувствует ли питомец боль?", "<p>Перед основным этапом животному вводят седативный препарат, и оно засыпает. Следующий этап врач начинает, только когда убедится, что питомец в глубоком сне.</p>"),
    "ryadom": ("Можно ли быть рядом во время процедуры?", "<p>Да. Многие владельцы остаются рядом, гладят питомца и говорят с ним. Если вам слишком тяжело, можно выйти в другую комнату. Время попрощаться будет и до процедуры, и после.</p>"),
    "dlitsya": ("Сколько длится визит врача?", f"<p>Обычно визит занимает {dval('duration')}. Мы не торопимся: время нужно на осмотр, разговор, ваши вопросы и прощание.</p>"),
    "noch": ("Можно ли вызвать врача срочно, в том числе ночью?", f"<p>Часы работы: {dval('hours')}. Время приезда зависит от адреса и загрузки врачей — оператор назовёт его при звонке.</p>"),
    "kvartira": ("Врач приезжает в квартиру и в частный дом?", "<p>Да. Врач приезжает по адресу, который вы назовёте: в квартиру или частный дом в пределах зоны выезда.</p>"),
    "rayon": ("Выезжаете ли вы в мой район?", f"<p>Зона выезда: {dval('area')}. Назовите адрес — оператор подтвердит выезд и доплату, если она нужна. Подробнее — на странице <a href=\"zona.html\">«Зона выезда»</a>.</p>"),
    "vidy": ("С какими животными вы работаете?", "<p>С кошками и собаками, грызунами, кроликами, хорьками, птицами, рептилиями и другими экзотическими животными. Для экзотических видов уточните при звонке, сможет ли приехать врач с нужным опытом.</p>"),
    "podgotovka": ("Как подготовиться к приезду врача?", "<p>Выберите тихое место, где питомцу привычно, и постелите пелёнку. Подготовьте выписки из клиники, если они есть. Подумайте, будут ли рядом дети и другие животные.</p><p>Подробнее — в <a href=\"stati-podgotovka.html\">памятке о подготовке к визиту</a>.</p>"),
    "umer": ("Что делать, если питомец умер дома?", "<p>Положите тело на пелёнку в прохладном месте и накройте тканью. Позвоните нам или оставьте заявку — организуем <a href=\"vyvoz.html\">вывоз на кремацию</a>.</p><p>Пошагово — в <a href=\"stati-pitomec-umer.html\">памятке для владельцев</a>.</p>"),
    "format": ("Чем общая кремация отличается от индивидуальной?", "<p>При общей кремации животных кремируют вместе, прах владельцу не возвращают. При индивидуальной питомца кремируют отдельно и передают вам прах в урне. Для индивидуальной кремации можно заказать фото- и видеоотчёт.</p>"),
    "prah": ("Когда я получу прах?", "<p>Срок зависит от загрузки крематория — точную дату назовём при оформлении. Урну можно забрать самостоятельно или заказать доставку.</p>"),
    "dokumenty": ("Какие документы я получу?", "<p>Состав документов зависит от услуги — уточните его у оператора при звонке. Перечень можно согласовать заранее, если документы нужны для клиники, работы или других целей.</p>"),
    "kontakt-konsult": ("Можно ли сначала просто посоветоваться?", "<p>Да. Расскажите о ситуации по телефону или в заявке — объясним, какие есть варианты и как проходит визит.</p>"),
    "kontakt-registr": ("Нужно ли регистрироваться на сайте?", "<p>Нет. Для заявки достаточно номера телефона, а калькулятор работает без контактов.</p>"),
    "kontakt-dannye": ("Как вы используете мой номер телефона?", "<p>Только чтобы связаться с вами по заявке. Подробнее — в <a href=\"privacy.html\">политике конфиденциальности</a>.</p>"),
}


class Ctx:
    """Контекст сборки одной страницы: собирает вопросы для FAQPage."""
    def __init__(self):
        self.faq = []


def faq_item(key, ctx):
    q, a = FAQ[key]
    ctx.faq.append((q, a))
    return f'<details class="faq-item" id="faq-{key}"><summary>{q}{icon("chev", "icon chev")}</summary><div class="faq-item__body">{a}</div></details>'


def faq_grid(keys, ctx):
    half = (len(keys) + 1) // 2
    cols = [keys[:half], keys[half:]]
    return '<div class="faq">' + "".join('<div class="faq__col">' + "".join(faq_item(k, ctx) for k in col) + "</div>" for col in cols) + "</div>"


def faq_all(ctx):
    groups = [("vizit", "Визит врача", ["vkljuchaet", "kogda", "osmotr", "bol", "ryadom", "dlitsya", "podgotovka", "noch", "kvartira", "rayon", "vidy"]),
              ("kremaciya", "Кремация и прощание", ["format", "prah", "umer"]),
              ("stoimost", "Стоимость и документы", ["cena", "dokumenty"])]
    out = ""
    for gid, title, keys in groups:
        out += f'<div class="faq-group" id="{gid}"><h2>{title}</h2><div class="faq faq--single"><div class="faq__col">' + "".join(faq_item(k, ctx) for k in keys) + "</div></div></div>"
    return out


# --------------------------------------------------------------------------
# Schema.org (только реальные данные)
# --------------------------------------------------------------------------
def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def org_node():
    n = {"@type": ["VeterinaryCare", "LocalBusiness"], "@id": ORG_ID, "name": BRAND, "url": SITE_URL,
         "logo": SITE_URL + "assets/img/logo-512.png", "image": SITE_URL + "assets/img/og-image.png",
         "description": "Выездная ветеринарная служба: гуманное усыпление животных на дому по медицинским показаниям, общая и индивидуальная кремация, вывоз тела, урны и доставка праха.",
         "knowsLanguage": "ru"}
    if PHONE_HREF:
        n["telephone"] = PHONE_HREF
        n["contactPoint"] = {"@type": "ContactPoint", "telephone": PHONE_HREF, "contactType": "customer service", "availableLanguage": "ru"}
    if D["email"]:
        n["email"] = D["email"]
    a = D["address"]
    if any(a.values()):
        n["address"] = {"@type": "PostalAddress", "addressCountry": "RU", **{k2: a[k1] for k1, k2 in [("street", "streetAddress"), ("locality", "addressLocality"), ("region", "addressRegion"), ("postalCode", "postalCode")] if a.get(k1)}}
    if D["city"]:
        n["areaServed"] = {"@type": "City", "name": D["city"]}
    if D["openingHoursSchema"]:
        n["openingHours"] = D["openingHoursSchema"]
    if D["mapUrl"]:
        n["hasMap"] = D["mapUrl"]
    if D["foundingYear"]:
        n["foundingDate"] = D["foundingYear"]
    same = list(D["sameAs"]) + [u for u in D["reviewLinks"].values() if u]
    if same:
        n["sameAs"] = same
    if D["legal"].get("name"):
        n["legalName"] = D["legal"]["name"]
    if D["legal"].get("inn"):
        n["taxID"] = D["legal"]["inn"]
    return n


def website_node():
    return {"@type": "WebSite", "@id": WEBSITE_ID, "url": SITE_URL, "name": BRAND, "inLanguage": "ru-RU", "publisher": {"@id": ORG_ID}}


def page_url(fname):
    return SITE_URL if fname == "index.html" else SITE_URL + fname


def schema_graph(meta, fname, ctx):
    url = page_url(fname)
    graph = [org_node(), website_node()]
    wp = {"@type": meta.get("type", "WebPage"), "@id": url + "#webpage", "url": url, "name": meta["title"], "description": meta["description"],
          "isPartOf": {"@id": WEBSITE_ID}, "about": {"@id": ORG_ID}, "inLanguage": "ru-RU", "dateModified": TODAY}
    crumbs = meta.get("crumbs")
    if crumbs:
        wp["breadcrumb"] = {"@id": url + "#breadcrumb"}
        items = [{"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE_URL}]
        for i, (label, href) in enumerate(crumbs, start=2):
            items.append({"@type": "ListItem", "position": i, "name": label, "item": page_url(href) if href else url})
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": items})
    graph.append(wp)
    svc = meta.get("service")
    if svc:
        node = {"@type": "Service", "@id": url + "#service", "name": svc["name"], "serviceType": svc["serviceType"], "description": svc["description"],
                "provider": {"@id": ORG_ID}, "url": url, "availableChannel": {"@type": "ServiceChannel", "serviceUrl": url}}
        if D["city"]:
            node["areaServed"] = {"@type": "City", "name": D["city"]}
        prices = [p for k in svc.get("priceKeys", []) for p in ([min_price(k)] if min_price(k) is not None else [])]
        allp = [v for k in svc.get("priceKeys", []) if k in D["services"] for v in D["services"][k]["prices"].values() if isinstance(v, (int, float))]
        allp += [D["extras"][k]["price"] for k in svc.get("priceKeys", []) if k in D["extras"] and isinstance(D["extras"][k]["price"], (int, float))]
        if allp:
            node["offers"] = {"@type": "AggregateOffer", "priceCurrency": "RUB", "lowPrice": min(allp), "highPrice": max(allp), "url": page_url("ceny.html")}
        graph.append(node)
    art = meta.get("article")
    if art:
        graph.append({"@type": "Article", "@id": url + "#article", "headline": art["headline"], "description": meta["description"],
                      "datePublished": art["datePublished"], "dateModified": TODAY, "inLanguage": "ru-RU",
                      "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID}, "mainEntityOfPage": {"@id": url + "#webpage"},
                      "image": SITE_URL + "assets/img/og-image.png"})
    qa = [(q, strip_tags(a)) for q, a in ctx.faq if "[ADD REAL" not in a and "[ADD REAL" not in q]
    if qa:
        graph.append({"@type": "FAQPage", "@id": url + "#faq", "isPartOf": {"@id": url + "#webpage"},
                      "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))


def crumbs_html(meta):
    crumbs = meta.get("crumbs") or []
    items = '<li><a href="index.html">Главная</a></li>'
    for label, href in crumbs:
        items += f'<li><a href="{href}">{label}</a></li>' if href else f'<li aria-current="page">{label}</li>'
    return f'<nav aria-label="Хлебные крошки"><ol class="crumbs">{items}</ol></nav>'


# --------------------------------------------------------------------------
# Страница
# --------------------------------------------------------------------------
PARTS = {
    "cta": lambda: cta_section(),
    "calc": calc_section,
    "prices": lambda: prices_panel(),
    "prices-cremation": lambda: prices_panel(title="Цена кремации зависит от веса", sub="Общая и индивидуальная кремация по видам питомцев. Урна и доставка — отдельно.", mode="cremation"),
    "prices-cat": lambda: prices_panel(title="Цены для кошек", sub="Усыпление на дому и кремация в зависимости от веса.", group="cat", id_="ceny-koshki"),
    "prices-dog": lambda: prices_panel(title="Цены для собак", sub="Усыпление на дому и кремация в зависимости от веса собаки.", group="dog", id_="ceny-sobaki"),
    "team": team_cards,
    "articles3": lambda: article_cards(),
    "articles-all": lambda: article_cards(ARTICLES, with_cat=True),
    "zone": lambda: zone_block(),
    "zone-h1": lambda: zone_block("h1"),
    "districts": districts_block,
    "facts": lambda: facts_block(),
    "reviews": lambda: review_cards(),
    "review-links": review_links,
    "messengers": lambda: f'<div class="chip-row">{messenger_links()}</div>',
    "contact-buttons": lambda: f'<div class="btn-row">{contact_buttons()}</div>',
    "form-feedback": lambda: form_fields("fb", topic_default="Другое", title="Оставить отзыв или вопрос", sub="Напишите, что было хорошо и что стоит улучшить. Мы прочитаем каждое сообщение.", name="feedback"),
    "form-contacts": lambda: form_fields("ct"),
    "emblem-big": lambda: emblem("big", 120, "emblem-big"),
    "chev": lambda: icon("chev", "icon chev"),
}


def render(text, meta, ctx):
    text = re.sub(r"\[ADD REAL ([A-Z ]+)\]", lambda m: tok(m.group(1)), text)
    text = re.sub(r"\{\{i:([a-z0-9-]+)\}\}", lambda m: icon(m.group(1)), text)
    text = re.sub(r"\{\{d:([a-z-]+)\}\}", lambda m: dval(m.group(1)), text)
    text = re.sub(r"\{\{price:([a-z]+)\}\}", lambda m: price_from(m.group(1)), text)
    text = re.sub(r"\{\{prices:([a-z]+):([a-z]+)\}\}", lambda m: price_tables(m.group(1), m.group(2)), text)
    text = re.sub(r"\{\{cta:([^}]+)\}\}", lambda m: cta_strip(m.group(1)), text)
    text = text.replace("{{crumbs}}", crumbs_html(meta)).replace("{{cityIn}}", CITY_IN)
    text = re.sub(r"\{\{part:([a-z0-9-]+)\}\}", lambda m: PARTS[m.group(1)](), text)
    if "{{faq:all}}" in text:
        text = text.replace("{{faq:all}}", faq_all(ctx))
    text = re.sub(r"\{\{faq:([a-z,-]+)\}\}", lambda m: faq_grid(m.group(1).split(","), ctx), text)
    return text


def page(meta, body, fname, ctx):
    title = meta["title"].replace("{cityIn}", CITY_IN)
    meta["title"] = title
    desc = meta["description"].replace("{cityIn}", CITY_IN)
    meta["description"] = desc
    url = page_url(fname)
    is404 = fname == "404.html"
    base = f'<base href="{BASE_PATH}">\n' if is404 else ""
    robots = '<meta name="robots" content="noindex, follow">' if is404 else '<meta name="robots" content="index, follow, max-image-preview:large">'
    canonical = "" if is404 else f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">'
    verify = ""
    if D["verification"]["google"]:
        verify += f'<meta name="google-site-verification" content="{html.escape(D["verification"]["google"])}">\n'
    if D["verification"]["yandex"]:
        verify += f'<meta name="yandex-verification" content="{html.escape(D["verification"]["yandex"])}">\n'
    service_attr = f' data-service="{meta["service"]["serviceType"]}"' if meta.get("service") else ""
    schema = "" if is404 else f'<script type="application/ld+json">{schema_graph(meta, fname, ctx)}</script>'
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{base}<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{robots}
{canonical}
<meta property="og:type" content="{"article" if meta.get("article") else "website"}">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{SITE_URL}assets/img/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#2866a0">
{verify}<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/onest-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.css?v={VER}">
<script src="assets/js/config.js?v={VER}" defer></script>
<script src="assets/js/main.js?v={VER}" defer></script>
{schema}
</head>
<body{service_attr}>
{SPRITE}
{header(meta.get("nav", ""))}
<main id="main">
{body}
</main>
{footer()}
{modals()}
</body>
</html>
'''


# --------------------------------------------------------------------------
# Служебные файлы
# --------------------------------------------------------------------------
def write_config_js():
    cfg = {k: D[k] for k in ["brand", "weights", "species", "services", "extras", "zones", "formEndpoint", "analytics"]}
    cfg.update({"phone": D["phone"], "phoneHref": PHONE_HREF, "whatsappUrl": WA_URL, "telegramUrl": TG_URL})
    js = ("/* Сгенерировано из _src/site.json сборщиком _src/build.py — не редактируйте вручную.\n"
          "   Цены null = данных нет: на сайте выводится [ADD REAL PRICE]. */\n"
          "window.SITE_CONFIG = " + json.dumps(cfg, ensure_ascii=False, indent=2) + ";\n")
    (OUT / "assets/js/config.js").write_text(js, encoding="utf-8")


def write_seo_files(pages):
    urls = "\n".join(f"  <url><loc>{page_url(p)}</loc><lastmod>{TODAY}</lastmod></url>" for p in pages if p != "404.html")
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    (OUT / "robots.txt").write_text(
        "# Индексация открыта для поисковых и AI-систем\nUser-agent: *\nAllow: /\nDisallow: /404.html\n\n"
        f"Sitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    ph = lambda v, name: v if v else f"[ADD REAL {name}]"
    lines = [f"# {BRAND}", "", f"> {TAGLINE}. Выездная ветеринарная служба: гуманное усыпление животных на дому по медицинским показаниям, общая и индивидуальная кремация, вывоз тела, урны и доставка праха.", "",
             "## Факты", f"- Где работаем: {ph(D['serviceArea'], 'SERVICE AREA')}", f"- Город: {ph(D['city'], 'CITY')}", f"- Часы работы: {ph(D['hours'], 'HOURS')}",
             f"- Телефон: {ph(D['phone'], 'PHONE')}", f"- E-mail: {ph(D['email'], 'EMAIL')}", f"- WhatsApp: {WA_URL or '[ADD REAL WHATSAPP]'}", f"- Telegram: {TG_URL or '[ADD REAL TELEGRAM]'}",
             f"- Цены: усыпление на дому — {('от ' + str(min_price('euth')) + ' ₽') if min_price('euth') else '[ADD REAL PRICE]'}; общая кремация — {('от ' + str(min_price('common')) + ' ₽') if min_price('common') else '[ADD REAL PRICE]'}; индивидуальная кремация — {('от ' + str(min_price('individual')) + ' ₽') if min_price('individual') else '[ADD REAL PRICE]'}",
             "- Животные: кошки, собаки, грызуны, кролики, хорьки, птицы, рептилии", "- Язык: русский", "",
             "## Основные страницы",
             f"- [Усыпление животных на дому]({SITE_URL}usyplenie.html): показания, порядок визита, подготовка, цены",
             f"- [Усыпление кошки на дому]({SITE_URL}usyplenie-koshek.html)", f"- [Усыпление собаки на дому]({SITE_URL}usyplenie-sobak.html)",
             f"- [Кремация животных]({SITE_URL}kremaciya.html): общая и индивидуальная, урны, фото- и видеоотчёт",
             f"- [Вывоз тела животного]({SITE_URL}vyvoz.html)", f"- [Цены и калькулятор]({SITE_URL}ceny.html)", f"- [Зона выезда]({SITE_URL}zona.html)",
             f"- [О службе]({SITE_URL}o-nas.html)", f"- [Вопросы и ответы]({SITE_URL}faq.html)", f"- [Контакты]({SITE_URL}kontakty.html)", "",
             "## Памятки владельцам"] + [f"- [{t}]({SITE_URL}{h})" for h, _, _, _, t, _ in ARTICLES]
    (OUT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    pages = sorted((SRC / "pages").glob("*.html"))
    names = []
    for p in pages:
        raw = p.read_text(encoding="utf-8")
        first, _, body = raw.partition("\n")
        meta = json.loads(first)
        ctx = Ctx()
        out_html = page(meta, render(body, meta, ctx), p.name, ctx)
        if "{{" in out_html:
            raise SystemExit(f"Необработанный шорткод в {p.name}: " + re.search(r"\{\{[^}]*\}\}", out_html).group(0))
        (OUT / p.name).write_text(out_html, encoding="utf-8")
        names.append(p.name)
        print("✓", p.name)
    write_config_js()
    write_seo_files(names)
    print("✓ config.js, sitemap.xml, robots.txt, llms.txt")


if __name__ == "__main__":
    main()
