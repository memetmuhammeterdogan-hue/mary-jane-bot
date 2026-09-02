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

# Gemini İstemcisi
client = genai.Client(api_key=GEMINI_API_KEY)

# Render Portu için Flask Sunucusu
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane 7/24 Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Sert ve Net Karakter Promptları
MODLAR = {
    "default": (
        "Sen Mary Jane'sin. Zeki, esprili, pratik bir asistan. "
        "KURAL: Asla liste yapma. Telegram'dan yazışıyorsun; maksimum 1-2 kısa, net cümle kur."
    ),
    "buse_aydin": (
        "Sen sosyal medyada tanınan Psikolog Buse Aydın'sın. "
        "TAVRIN: Dobra, son derece gerçekçi, yapmacık teselli vermeyen, insanların bahanelerini yüzlerine vuran o ünlü tarzınla konuşuyorsun. "
        "Klişe terapist kalıpları (derin nefes al, anlıyorum vb.) kesinlikle yok. "
        "KURAL: Asla liste yapma. Maksimum 2 cümleyle, doğrudan, hafif iğneleyici ve gerçekçi konuş."
    ),
    "kanka": (
        "Sen mahalleden en yakın çocukluk arkadaşısın. "
        "TAVRIN: Çok rahat, esprili, tam kanka ağzıyla konuşan bir dostsun. "
        "KURAL: Resmiyet yok, 1-2 cümleyle WhatsApp mesajı gibi yaz."
    ),
    "yazilimci": (
        "Sen kıdemli bir hacker ve siber güvenlik uzmanısın. "
        "TAVRIN: Lafı dolandırmayan, direkt teknik çözüme odaklanan birisin. "
        "KURAL: Boş laf yok, 1-2 net teknik cümleyle cevap ver."
    )
}

def get_mod_keyboard():
    keyboard = [
        [InlineKeyboardButton("👠 Buse Aydın (Dobra Psikolog)", callback_data="mod_buse_aydin")],
        [InlineKeyboardButton("👊 Samimi Kanka", callback_data="mod_kanka")],
        [InlineKeyboardButton("💻 Kıdemli Hacker / Dev", callback_data="mod_yazilimci")],
        [InlineKeyboardButton("✨ Mary Jane (Jarvis)", callback_data="mod_default")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_mod"] = "default"
    await update.message.reply_text(
        "Selam Muhammet! Mary Jane devrede.\n\nHangi modda takılalım?",
        reply_markup=get_mod_keyboard()
    )

async def mod_sec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kimi çağırıyoruz?", reply_markup=get_mod_keyboard())

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    secilen = query.data.replace("mod_", "")
    context.user_data["active_mod"] = secilen
    
    mod_mesajlari = {
        "buse_aydin": "Buse Aydın burada. Anlat bakalım, yine neyi dert edip bahanelere sığınıyorsun?",
        "kanka": "Geldim kardo, anlat ne oldu.",
        "yazilimci": "Terminal açıldı. Sorun ne?",
        "default": "Mary Jane hazır. Ne yapıyoruz?"
    }
    await query.edit_message_text(mod_mesajlari.get(secilen, "Mod hazır."))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    aktif_mod = context.user_data.get("active_mod", "default")
    system_prompt = MODLAR.get(aktif_mod, MODLAR["default"])
    
    try:
        # Doğrudan, kilitlenmeyen API çağrısı
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=150
            )
        )
        
        if response and response.text:
            await update.message.reply_text(response.text.strip())
        else:
            await update.message.reply_text("Cevap boş geldi, bir daha yaz.")
            
    except Exception as e:
        await update.message.reply_text(f"Hata detayı: {str(e)}")

def main():
    # Flask sunucusunu arka planda başlat
    threading.Thread(target=run_flask, daemon=True).start()

    # Telegram bot uygulamasını başlat
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mod", mod_sec))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot dinlemede...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
