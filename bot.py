from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import requests
import os
import json

API_ID = 23346001
API_HASH = "08c63cda730a00374392062e09c426d1"
BOT_TOKEN = "8161140522:AAHHIJaLYmlPCsTJrInDxDRfKWTfzXaMDXI"
TOGETHER_API_KEY = "10888df0044c2a80602f2b4238e376fdd95fc62a6ab824b265a074ff5b1b1fe9"
TOGETHER_MODEL = "deepseek-ai/DeepSeek-V3"
ADMIN_IDS = [7181480233]
CHANNELS = ["@texno_yangiliklr_UZ", "@kompyuterishlaridastirlar"]
DATA_FILE = "user_data.json"

MESSAGE_LIMIT = 10
TIME_WINDOW = 2 * 60 * 60  # 2 soat

app = Client("deepseek_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

data = load_data()

@app.on_message(filters.command("start") & filters.private)
def start(client, message):
    user_id = str(message.from_user.id)

    if user_id not in data:
        data[user_id] = {"lang": None, "timestamps": []}
        save_data(data)

    keyboard = ReplyKeyboardMarkup(
        [["🇺🇿 O‘zbekcha", "🇷🇺 Русский", "🇬🇧 English"]],
        resize_keyboard=True, one_time_keyboard=True
    )
    message.reply_text("🌐 Iltimos, tilni tanlang:\n\nPlease choose your language:", reply_markup=keyboard)

@app.on_message(filters.text & filters.private)
def handle_message(client, message):
    user_id = str(message.from_user.id)
    text = message.text

    if user_id not in data:
        data[user_id] = {"lang": None, "timestamps": []}
        save_data(data)

    if data[user_id]["lang"] is None:
        if text == "🇺🇿 O‘zbekcha":
            data[user_id]["lang"] = "uz"
        elif text == "🇷🇺 Русский":
            data[user_id]["lang"] = "ru"
        elif text == "🇬🇧 English":
            data[user_id]["lang"] = "en"
        else:
            message.reply_text("❗️ Iltimos, tilni tanlang.")
            return

        save_data(data)

        buttons = [
            [InlineKeyboardButton(ch[1:], url=f"https://t.me/{ch[1:]}")] for ch in CHANNELS
        ]
        buttons.append([InlineKeyboardButton("✅ Davom etish", callback_data="continue")])
        message.reply_text("📢 Quyidagi kanallarga obuna bo‘ling va davom eting:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    now = time.time()
    timestamps = [t for t in data[user_id]["timestamps"] if now - t < TIME_WINDOW]

    if len(timestamps) >= MESSAGE_LIMIT:
        lang = data[user_id]["lang"]
        messages = {
            "uz": "⏳ 2 soatda 10 ta savol berishingiz mumkin. Keyinroq urinib ko‘ring.",
            "ru": "⏳ Вы задали 10 вопросов за 2 часа. Пожалуйста, попробуйте позже.",
            "en": "⏳ You've asked 10 questions in 2 hours. Please try again later."
        }
        message.reply_text(messages.get(lang, "⏳ Limit reached. Try later."))
        return

    try:
        wait_msg = message.reply_text("🔄 Ma’lumotlar to‘planmoqda...")

        reply = ask_deepseek(text)
        wait_msg.edit_text(reply)

        timestamps.append(now)
        data[user_id]["timestamps"] = timestamps
        save_data(data)

        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {user_id}: {text}\n"
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception as e:
        print(f"Xato: {e}")
        message.reply_text("❌ Javobni olishda xatolik. Keyinroq urinib ko‘ring.")

@app.on_callback_query(filters.regex("continue"))
def continue_handler(client, callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    lang = data.get(user_id, {}).get("lang", "uz")
    texts = {
        "uz": "✅ Botga xush kelibsiz! Endi savolingizni yozishingiz mumkin.",
        "ru": "✅ Добро пожаловать! Можете отправить свой вопрос.",
        "en": "✅ Welcome! You can now ask your question."
    }
    callback_query.message.reply_text(texts.get(lang, "✅ You can now chat."))
    callback_query.answer()

def ask_deepseek(prompt):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": TOGETHER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 100  # Qisqaroq javoblar uchun
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

@app.on_message(filters.command("stat") & filters.private)
def show_stats(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    message.reply_text(f"📊 Umumiy foydalanuvchilar: {len(data)}")

@app.on_message(filters.command("logs") & filters.private)
def show_logs(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not os.path.exists("log.txt"):
        message.reply_text("📂 Log fayli topilmadi.")
        return
    with open("log.txt", "r", encoding="utf-8") as f:
        logs = f.readlines()[-30:]
    message.reply_text("📝 Oxirgi savollar:\n\n" + "".join(logs))

print("✅ DeepSeek bot ishga tushdi!")
app.run()
     malumotlar to'planmoqda
