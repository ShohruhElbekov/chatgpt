import json
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import openai

api_id = 123456  # o‘zingizning API_ID
api_hash = "your_api_hash"
bot_token = "your_bot_token"

openai.api_key = "your_openai_api_key"

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

MAX_QUESTIONS = 10
TIME_WINDOW = 2 * 60 * 60  # 2 soat

# JSON fayl orqali savol sonini saqlash
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# DeepSeek (GPT-3.5) API so‘rovi
def ask_deepseek(prompt):
    max_tokens = 100 if len(prompt) < 20 else 250 if len(prompt) < 100 else 400
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # yoki together ai modeli
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response["choices"][0]["message"]["content"]

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text("🤖 Salom! Savolingizni yuboring. Siz har 2 soatda 10 tagacha savol bera olasiz.")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_question(client, message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    now = time.time()

    data = load_data()
    user = data.get(user_id, {"timestamps": []})
    timestamps = [ts for ts in user["timestamps"] if now - ts < TIME_WINDOW]

    if len(timestamps) >= MAX_QUESTIONS:
        await message.reply_text("🚫 Siz 2 soat ichida 10 ta savoldan ortig‘ini berdingiz. Iltimos, keyinroq urinib ko‘ring.")
        return

    # Foydalanuvchi typing... holatini ko‘rsatish
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Foydalanuvchiga kutish xabari
    processing_msg = await message.reply_text("⏳ Ma'lumotlar to‘planmoqda...")

    try:
        reply = ask_deepseek(text)
        await processing_msg.edit_text(reply)

        # Yangi timestampni qo‘shish
        timestamps.append(now)
        data[user_id] = {"timestamps": timestamps}
        save_data(data)

        # Log faylga yozish
        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {user_id}: {text}\n"
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Foydalanuvchi ID | username ni saqlash
        with open("users.txt", "a", encoding="utf-8") as f:
            user_username = f"@{message.from_user.username}" if message.from_user.username else "NoUsername"
            line = f"{user_id} | {user_username}\n"
            if line not in open("users.txt", encoding="utf-8").read():
                f.write(line)

    except Exception as e:
        print(f"Xato: {e}")
        await processing_msg.edit_text("❌ Javobni olishda xatolik. Iltimos, keyinroq urinib ko‘ring.")

app.run()
