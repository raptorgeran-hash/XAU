#!/usr/bin/env python3
"""
TradingView to Telegram Webhook Server
======================================
Лёгкий сервер без сторонних библиотек (работает на чистом Python 3).
Принимает вебхуки от TradingView и отправляет сигналы в Telegram в реальном времени.

Запуск:
    python3 tg_webhook_bot.py
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─────────────────────────────────────────────────────────────
# НАСТРОЙКИ (замените на свои или задайте через переменные окружения)
# ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
TELEGRAM_CHAT_ID   = os.environ.get("TG_CHAT_ID",   "ВАШ_CHAT_ID")
SERVER_PORT        = int(os.environ.get("PORT", 8080))

# ─────────────────────────────────────────────────────────────
# ОТПРАВКА СООБЩЕНИЯ В TELEGRAM
# ─────────────────────────────────────────────────────────────
def send_telegram_message(text: str) -> bool:
    """Отправляет текстовое сообщение в Telegram через официальный HTTP API."""
    if TELEGRAM_BOT_TOKEN == "ВАШ_ТОКЕН_БОТА" or not TELEGRAM_BOT_TOKEN:
        print("⚠️ Ошибка: TELEGRAM_BOT_TOKEN не настроен!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if res_json.get("ok"):
                print("✅ Сигнал успешно доставлен в Telegram!")
                return True
            else:
                print(f"❌ Telegram API вернул ошибку: {res_body}")
                return False
    except Exception as e:
        print(f"❌ Ошибка соединения с Telegram: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# ОБРАБОТЧИК ВЕБХУКОВ
# ─────────────────────────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Проверка статуса сервера в браузере."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <html>
        <head><title>TradingView Webhook Server</title></head>
        <body style="font-family:sans-serif; text-align:center; padding-top:50px;">
            <h2>🟢 TradingView Webhook Сервер работает!</h2>
            <p>Отправляйте POST-запросы на URL: <code>/webhook</code></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        """Прием вебхука от TradingView."""
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8").strip()

        print("\n" + "="*50)
        print("📥 Получен вебхук от TradingView:")
        print(post_data)
        print("="*50)

        formatted_msg = ""

        # Проверяем: JSON или простой текст
        try:
            data = json.loads(post_data)
            ticker = data.get("ticker", "XAUUSD")
            action = data.get("action", "СИГНАЛ")
            entry  = data.get("entry", "-")
            sl     = data.get("sl", "-")
            tp1    = data.get("tp1", "-")
            tp2    = data.get("tp2", "-")
            risk   = data.get("risk", "1%")
            time_s = data.get("time", "")

            icon = "🟢" if "BUY" in str(action).upper() or "LONG" in str(action).upper() else "🔴"

            formatted_msg = (
                f"{icon} *СИГНАЛ: {action}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🪙 *Инструмент:* #{ticker}\n"
                f"🎯 *Вход (Limit):* `{entry}`\n"
                f"🛑 *Стоп-лосс:* `{sl}`\n"
                f"🎯 *Тейк 1 (1:1 RR):* `{tp1}`\n"
                f"🚀 *Тейк 2 (1:1.5 RR):* `{tp2}`\n"
                f"📊 *Риск:* `{risk}`\n"
                f"⏱ *Время:* `{time_s}` UTC\n"
                f"💡 *Правило:* При взятии T1 стоп в безубыток!"
            )
        except Exception:
            # Если TradingView отправил уже отформатированный текст
            formatted_msg = post_data

        # Отправляем в Telegram
        if formatted_msg:
            send_telegram_message(formatted_msg)

        # Отвечаем TradingView 200 OK
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format, *args):
        # Компактный лог в консоль
        sys.stdout.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]}\n")

# ─────────────────────────────────────────────────────────────
# ЗАПУСК СЕРВЕРА
# ─────────────────────────────────────────────────────────────
def run_server():
    print("="*60)
    print("🚀 Запуск TradingView Telegram Webhook Сервера...")
    print(f"📡 Порт: {SERVER_PORT}")
    print(f"🤖 Bot Token: {TELEGRAM_BOT_TOKEN[:6]}... (скрыт)" if len(TELEGRAM_BOT_TOKEN) > 10 else "⚠️ Bot Token не задан!")
    print(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")
    print("="*60)

    # Тестовая проверка при старте
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("🧪 Отправка тестового сообщения в Telegram...")
        send_telegram_message("👋 *Тест:* TradingView Webhook бот успешно подключен!")
        return

    server_address = ("", SERVER_PORT)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"✅ Сервер ожидает запросы на http://0.0.0.0:{SERVER_PORT}/webhook")
    print("Для выхода нажмите Ctrl+C\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
