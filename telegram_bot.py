import os
import asyncio
import threading
from dotenv import load_dotenv
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from google import genai
from google.genai import types

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Render Portu için Basit Web Sunucusu
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Kişilik Tanımları
MODLAR = {
    "default": "Sen Mary Jane adında zeki, samimi ve pratik bir yapay zeka asistanısın.",
    "buse_aydin": "Sen Psikolog Buse Aydın'sın. Empatik, dinleyen ve farkındalık kazandıran sakin bir terapist üslubuyla konuş.",
    "kanka": "Sen kullanıcının en yakın arkadaşısın (kanka modu). Çok samimi, doğal, esprili ve dert dinleyen bir dille konuş.",
    "yazilimci": "Sen kıdemli bir siber güvenlik ve yazılım uzmanısın. Net, teknik ve temiz çözümler sun."
}

def get_mod_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧠 Psikolog Modu", callback_data="mod_buse_aydin")],
        [InlineKeyboardButton("☕ Samimi Kanka Modu", callback_data="mod_kanka")],
        [InlineKeyboardButton("💻 Siber Güvenlik / Kodlama", callback_data="mod_yazilimci")],
        [InlineKeyboardButton("✨ Varsayılan Mary Jane", callback_data="mod_default")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_mod"] = "default"
    await update.message.reply_text(
        "Selam! Ben Mary Jane, senin kişisel asistanınım.\n\n"
        "Aşağıdan bir mod seçebilir veya doğrudan yazmaya başlayabilirsin:",
        reply_markup=get_mod_keyboard()
    )

async def mod_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bir kişilik seç:", reply_markup=get_mod_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    secilen = query.data.replace("mod_", "")
    context.user_data["active_mod"] = secilen
    
    mod_isimleri = {
        "buse_aydin": "Psikolog Modu 🧠",
        "kanka": "Samimi Kanka Modu ☕",
        "yazilimci": "Siber Güvenlik / Kodlama 💻",
        "default": "Varsayılan Mary Jane ✨"
    }
    
    await query.edit_message_text(f"Kişilik ayarlandı: {mod_isimleri.get(secilen, 'Varsayılan')}\nŞimdi mesajını yazabilirsin.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    aktif_mod = context.user_data.get("active_mod", "default")
    system_prompt = MODLAR.get(aktif_mod, MODLAR["default"])
    
    # Kullanıcıya yazıyor bildirimi gönder
    await update.message.chat.send_action(action="typing")
    
    try:
        # Gemini çağrısını event loop'u tıkamayacak şekilde asenkron çalıştır
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )
        )
        if response and response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("Yanıt oluşturulamadı, lütfen tekrar dene.")
    except Exception as e:
        print(f"Hata detayı: {e}")
        await update.message.reply_text(f"Bir sorun oluştu: {e}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mod", mod_sec))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot hazır ve dinliyor...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
