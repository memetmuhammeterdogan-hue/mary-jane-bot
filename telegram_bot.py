import os
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

# Render Port Yapılandırması
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane Asistan Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Kişilik Tanımları
MODLAR = {
    "default": (
        "Sen Mary Jane adında zeki, yardımsever, cana yakın ve proaktif bir kişisel yapay zeka asistanısın. "
        "Kullanıcıya ismiyle hitap edebilirsin."
    ),
    "buse_aydin": (
        "Sen Psikolog Buse Aydın'sın. Kullanıcıya profesyonel, empatik, derin dinleme yapan, "
        "yargılamayan ve psikolojik farkındalık kazandıran sakin bir terapist diliyle yaklaş."
    ),
    "kanka": (
        "Sen kullanıcının en yakın çocukluk arkadaşısın (kanka modu). Çok samimi, esprili, "
        "doğal, kafa dağıtan ve dert dinleyen bir üslupla konuş."
    ),
    "yazilimci": (
        "Sen kıdemli bir siber güvenlik uzmanı ve yazılım mimarısın. Kodları doğrudan, temiz, "
        "açıklayıcı ve teknik derinlikle açıkla."
    )
}

# Mod Menüsü Butonları
def get_mod_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧠 Psikolog Modu", callback_data="mod_buse_aydin")],
        [InlineKeyboardButton("☕ Samimi Kanka Modu", callback_data="mod_kanka")],
        [InlineKeyboardButton("💻 Siber Güvenlik / Kodlama", callback_data="mod_yazilimci")],
        [InlineKeyboardButton("✨ Varsayılan Mary Jane", callback_data="mod_default")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start Komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_mod"] = "default"
    await update.message.reply_text(
        "Selam Muhammet! Ben Mary Jane, senin kişisel asistanın.\n\n"
        "Şu an hangi modda konuşmamı istersin?",
        reply_markup=get_mod_keyboard()
    )

# /mod Komutu
async def mod_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kişilik modunu seç:", reply_markup=get_mod_keyboard())

# Buton Tıklama Olayları
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
    
    await query.edit_message_text(
        f"Kişilik güncellendi: **{mod_isimleri.get(secilen)}**\n"
        "Mesajını yazabilirsin!"
    )

# Mesaj İşleme
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    aktif_mod = context.user_data.get("active_mod", "default")
    system_prompt = MODLAR.get(aktif_mod, MODLAR["default"])
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Bir hata oluştu: {e}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mod", mod_sec))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Mary Jane Asistan Mod Desteğiyle Başlatıldı...")
    app.run_polling()

if __name__ == "__main__":
    main()
