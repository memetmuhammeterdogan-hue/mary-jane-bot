import os
import threading
from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini istemcisi
client = genai.Client(api_key=GEMINI_API_KEY)

# Render port kontrolü için küçük Flask sunucusu
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane Bot Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Telegram komut ve mesaj yakalayıcıları
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Ben Mary Jane, senin kişisel AI asistanınım.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_text,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Bir hata oluştu: {e}")

def main():
    # Flask sunucusunu arka planda başlat
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram botunu başlat
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Mary Jane Telegram Botu Çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
