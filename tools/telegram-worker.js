/* Пересылка заявок с сайта в Telegram (Cloudflare Worker).
   Секреты задаются в панели Cloudflare, в код их не вписывать:
     BOT_TOKEN — токен бота от @BotFather
     CHAT_ID   — id чата или группы, куда приходят заявки
     ALLOWED_ORIGIN — адрес сайта без слеша, например https://diego001-art.github.io
   Адрес воркера после публикации вписать в formEndpoint в _src/site.json. */

const FIELDS = [
  ["topic", "Тема"],
  ["name", "Имя"],
  ["phone", "Телефон"],
  ["location", "Адрес / район"],
  ["time", "Удобное время"],
  ["details", "Расчёт"],
  ["page", "Страница"],
];

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: cors });
    if (env.ALLOWED_ORIGIN && origin !== env.ALLOWED_ORIGIN) return new Response("Forbidden", { status: 403, headers: cors });

    let data;
    try { data = await request.json(); } catch { return new Response("Bad request", { status: 400, headers: cors }); }
    const digits = String(data.phone || "").replace(/\D/g, "");
    if (digits.length !== 11 || !data.consent) {
      return new Response("Bad request", { status: 400, headers: cors });
    }

    const lines = ["<b>Новая заявка с сайта</b>"];
    for (const [key, label] of FIELDS) {
      const v = String(data[key] || "").trim().slice(0, 500);
      if (v) lines.push(`<b>${label}:</b> ${esc(v)}`);
    }
    lines.push("Согласие на обработку данных: получено");

    const tg = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: env.CHAT_ID, text: lines.join("\n"), parse_mode: "HTML" }),
    });
    return new Response(tg.ok ? "ok" : "telegram error", { status: tg.ok ? 200 : 502, headers: cors });
  },
};
