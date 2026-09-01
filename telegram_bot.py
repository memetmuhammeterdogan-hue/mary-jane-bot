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

# Render portu için web sunucusu
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane Bot Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# Karakter ve Kişilik Tanımları
MODLAR = {
    "default": (
        "Sen Mary Jane adında zeki, yardımsever, cana yakın ve çok yönlü bir yapay zeka asistanısın."
    ),
    "buse_aydin": (
        "Sen Psikolog Buse Aydın'sın. Kullanıcıya profesyonel, empatik, derin dinleme yapan, "
        "yargılamayan ve psikolojik farkındalık kazandıran bir terapist diliyle yaklaş."
    ),
    "kanka": (
        "Sen kullanıcının en yakın çocukluk arkadaşısın (kanka modu). Çok samimi, doğal, "
        "esprili, yeri geldiğinde kafa dağıtan ve dert dinleyen bir üslupla konuş."
    ),
    "yazilimci": (
        "Sen kıdemli bir siber güvenlik uzmanı ve yazılım mimarısın. Kodları doğrudan, temiz, "
        "açıklayıcı ve teknik derinlikle açıkla."
    )
}

# Mod Seçim Menüsü
def get_mod_keyboard():
    keyboard = [
        [InlineKeyboardButton("🧠 Psikolog Buse Aydın", callback_data="mod_buse_aydin")],
        [InlineKeyboardButton("☕ Samimi Arkadaş (Kanka)", callback_data="mod_kanka")],
        [InlineKeyboardButton("💻 Siber Güvenlik / Yazılımcı", callback_data="mod_yazilimci")],
        [InlineKeyboardButton("✨ Varsayılan Mary Jane", callback_data="mod_default")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_mod"] = "default"
    await update.message.reply_text(
        "Merhaba! Ben Mary Jane.\n\n"
        "Benimle nasıl konuşmak istersin? Aşağıdaki modlardan birini seçebilirsin:",
        reply_markup=get_mod_keyboard()
    )

# /mod komutu ile menüyü tekrar çağırma
async def mod_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Geçmek istediğin modu seç:", reply_markup=get_mod_keyboard())

# Buton tıklamalarını yakalama
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    secilen = query.data.replace("mod_", "")
    context.user_data["active_mod"] = secilen
    
    mod_isimleri = {
        "buse_aydin": "Psikolog Buse Aydın 🧠",
        "kanka": "Samimi Arkadaş ☕",
        "yazilimci": "Siber Güvenlik / Yazılımcı 💻",
        "default": "Varsayılan Mary Jane ✨"
    }
    
    await query.edit_message_text(f"Mod başarıyla değiştirildi: **{mod_isimleri.get(secilen)}**\nŞimdi dilediğin gibi konuşabilirsin!")

# Mesaj yanıtlama
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
    
    print("Mary Jane Telegram Botu Mod Desteğiyle Çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
