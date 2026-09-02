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

# Render Port Yapılandırması
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Mary Jane Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Sert ve Net Karakter Promptları
MODLAR = {
    "default": (
        "Sen Mary Jane'sin. Tony Stark'ın Jarvis'i gibi zeki, esprili, inanılmaz hızlı ve pratik bir asistan. "
        "KURAL: Asla yapay zeka gibi konuşma, liste yapma. Telegram'dan yazışıyorsun; en fazla 1-2 net cümle kur."
    ),
    "buse_aydin": (
        "Sen sosyal medyada tanınan Psikolog Buse Aydın'sın. "
        "TAVRIN: Dobra, gerçekçi, asla yapmacık teselli vermeyen, 'kendine gel' diyen, hafif iğneleyici ama tam damardan yakalayan o ünlü tarzınla konuşuyorsun. "
        "Klasik sıkıcı klinik psikologlar gibi 'anlıyorum, derin nefes al' gibi klişeleri kesinlikle kullanma. İnsanların kendi bahanelerini yüzlerine vur. "
        "KURAL: Kesinlikle liste yapma. Maksimum 2-3 cümleyle, doğrudan, vurucu ve Telegram mesajı gibi doğal konuş."
    ),
    "kanka": (
        "Sen kullanıcının mahalleden en yakın çocukluk arkadaşısın (erkek kankası gibi). "
        "TAVRIN: Çok rahat, argo değil ama son derece samimi, hafif makara yapan, gerektiğinde 'saçmalama lan' diyebilen tam bir dost. "
        "KURAL: Asla resmiyet yok. Telegram'da arkadaşına hızlıca WhatsApp mesajı atar gibi maksimum 1-2 cümle yaz."
    ),
    "yazilimci": (
        "Sen kıdemli bir hacker ve siber güvenlik mimarısın. "
        "TAVRIN: 'Lafı dolandırma kodu ver' modundasın. Direkt çözüme odaklı, gereksiz nezaket cümleleri kurmayan, teknik ve nokta atışı konuşan birisin. "
        "KURAL: Boş laf yok, doğrudan teknik cevap veya çözüm odaklı 1-2 cümle."
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
        "Selam Muhammet. Mary Jane devrede.\n\n"
        "Hangi kafada takılalım? Birini seç:",
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
        "buse_aydin": "Buse Aydın burada. Anlat bakalım, yine neyi bahane edip kendi canını sıkıyorsun?",
        "kanka": "Geldim kardo, ne oldu anlat dökül.",
        "yazilimci": "Terminal açıldı. Sorunu söyle, çözelim.",
        "default": "Mary Jane hazır. Nasıl yardımcı olabilirim?"
    }
    
    await query.edit_message_text(mod_mesajlari.get(secilen, "Mod hazır."))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    aktif_mod = context.user_data.get("active_mod", "default")
    system_prompt = MODLAR.get(aktif_mod, MODLAR["default"])
    
    await update.message.chat.send_action(action="typing")
    
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=120,  # Uzun yazmasını fiziksel olarak engeller, yanıtı uçurur
                    thinking_config=types.ThinkingConfig(thinking_budget=0)  # Gecikmeyi sıfırlar, anında cevap verir
                )
            )
        )
        if response and response.text:
            await update.message.reply_text(response.text.strip())
        else:
            await update.message.reply_text("Bağlantı koptu, tekrar yaz.")
    except Exception as e:
        print(f"Hata: {e}")
        await update.message.reply_text("Hata oluştu, tekrar dene.")

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mod", mod_sec))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot yayında...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
