import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google import genai
from google.genai.errors import APIError

# ========================================================================
# 1. KONFIGURATSIYA QISMI (Render muhitiga moslashgan)
# ========================================================================

# BOT_TOKEN va GEMINI_API_KEY Render muhitida Environment Variables orqali olinadi.
# Hozircha bu yerda sinov uchun qoldiramiz, lekin keyin serverda alohida sozlanadi.
BOT_TOKEN = "8331826386:AAFo4TqHrxk3nkJ66BNF5wGLenGlM4Qvthc" 
GEMINI_API_KEY = "AIzaSyDy4W2dLAs2LoErO6i28SefKmIe9U2Rz9I" 
CHANNEL_ID = "-1002494664955"  # Topilgan Kanal ID

# --- Gemini AI Modelini Sozlash ---
client = None
MODEL_NAME = 'gemini-2.5-flash'
model_status = False 

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini APIga muvaffaqiyatli ulanildi.")
    model_status = True
except Exception as e:
    print(f"!!! DIQQAT !!! Gemini APIga ulanishda xato yuz berdi: {e}")
    model_status = False

# ========================================================================
# 2. XABARLAR LUG'ATI (TILGA MOSLASH UCHUN)
# ========================================================================

MESSAGES = {
    'uz': {
        'prompt_subscribe': "Botdan foydalanishdan oldin, iltimos, rasmiy kanalimizga obuna bo'ling:",
        'btn_subscribe': "📢 Kanalga Obuna Bo'lish",
        'btn_check': "✅ Obuna Bo'ldim / Tekshirish",
        'lang_selected': "Til: O'zbekcha tanlandi.",
        'sub_success': "✅ Obuna tekshiruvidan muvaffaqiyatli o'tdingiz!\nEndi botdan foydalanishingiz mumkin. Savolingizni yuboring.",
        'sub_failed_title': "❌ Kechirasiz, obuna topilmadi.",
        'sub_failed_body': "Iltimos, kanalga obuna bo'lganingizga ishonch hosil qiling va qayta urinib ko'ring.",
        'ai_down': "Kechirasiz, AI xizmati hozirda ishlamayapti.",
        'ai_error': "AI so'rovida xato yuz berdi. Iltimos, API kalitingizni tekshiring.",
        'unknown_error': "Kechirasiz, kutilmagan xato yuz berdi.",
        'choose_lang': 'Tilni tanlang / Выберите язык / Choose language:',
    },
    'ru': {
        'prompt_subscribe': "Прежде чем использовать бота, пожалуйста, подпишитесь на наш официальный канал:",
        'btn_subscribe': "📢 Подписаться на канал",
        'btn_check': "✅ Я подписался / Проверить",
        'lang_selected': "Язык: Русский выбран.",
        'sub_success': "✅ Проверка подписки прошла успешно!\nТеперь вы можете пользоваться ботом. Отправьте свой вопрос.",
        'sub_failed_title': "❌ Извините, подписка не найдена.",
        'sub_failed_body': "Пожалуйста, убедитесь, что вы подписаны на канал, и попробуйте снова.",
        'ai_down': "Извините, служба ИИ в настоящее время не работает.",
        'ai_error': "Произошла ошибка запроса ИИ. Пожалуйста, проверьте ваш ключ API.",
        'unknown_error': "Извините, произошла непредвиденная ошибка.",
        'choose_lang': 'Tilni tanlang / Выберите язык / Choose language:',
    },
    'en': {
        'prompt_subscribe': "Before using the bot, please subscribe to our official channel:",
        'btn_subscribe': "📢 Subscribe to Channel",
        'btn_check': "✅ Subscribed / Check",
        'lang_selected': "Language: English selected.",
        'sub_success': "✅ Subscription check successful!\nYou can now use the bot. Send your question.",
        'sub_failed_title': "❌ Sorry, subscription not found.",
        'sub_failed_body': "Please make sure you are subscribed to the channel and try again.",
        'ai_down': "Sorry, the AI service is currently unavailable.",
        'ai_error': "An AI request error occurred. Please check your API key.",
        'unknown_error': "Sorry, an unexpected error occurred.",
        'choose_lang': 'Tilni tanlang / Выберите язык / Choose language:',
    }
}

# ========================================================================
# 3. Yordamchi Funksiyalar
# ========================================================================

async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Foydalanuvchining kanalga obuna bo'lganligini tekshiradi."""
    if not CHANNEL_ID:
        return True 

    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Kanal a'zoligini tekshirishda xato: {e}")
        return False


def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Foydalanuvchi tanlagan tilni (yoki standart 'uz' ni) oladi."""
    return context.user_data.get('lang', 'uz')

async def subscription_check_message(update_or_query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Obunani tekshirish tugmasi bilan tilga mos xabar yuboradi."""
    
    lang_code = get_user_lang(context)
    msg = MESSAGES.get(lang_code, MESSAGES['uz'])
    
    if isinstance(update_or_query, Update):
        effective_message = update_or_query.effective_message
    else:
        effective_message = update_or_query.message

    try:
        chat_info = await context.bot.get_chat(CHANNEL_ID)
        channel_link = chat_info.invite_link or f"https://t.me/{chat_info.username}"
    except Exception:
        channel_link = "https://t.me/"

    channel_link_button = InlineKeyboardButton(msg['btn_subscribe'], url=channel_link)
    check_button = InlineKeyboardButton(msg['btn_check'], callback_data="check_subscription")
    
    keyboard = InlineKeyboardMarkup([[channel_link_button], [check_button]])
    
    await effective_message.reply_text(
        msg['prompt_subscribe'],
        reply_markup=keyboard
    )


async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Til tanlash tugmalarini yuboradi."""
    
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(MESSAGES['uz']['choose_lang'], reply_markup=reply_markup)

# ========================================================================
# 4. Telegram Handler Funksiyalari
# ========================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi /start buyrug'ini yuborganida til tanlashni ko'rsatadi."""
    context.user_data['lang'] = 'uz' 
    await language_selection(update, context)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline tugmalarni bosishni boshqaradi (Til tanlash, Obunani tekshirish)."""
    query = update.callback_query
    await query.answer() 
    
    user_id = query.from_user.id
    data = query.data
    
    # --- Tilni tanlash ---
    if data.startswith("lang_"):
        new_lang_code = data.split('_')[1]
        context.user_data['lang'] = new_lang_code
        lang_code = new_lang_code
        msg = MESSAGES.get(lang_code, MESSAGES['uz'])
        
        # 1. Xabarni tahrirlaymiz
        await query.edit_message_text(msg['lang_selected'])

        # 2. Obunani tekshirish
        if await is_subscribed(user_id, context):
            await query.message.reply_text(msg['sub_success']) # <--- Tilga mos muvaffaqiyat xabari
        else:
            # Obuna bo'lmagan bo'lsa, kanalga yo'naltirish
            await subscription_check_message(query, context)
            
    # --- Obunani tekshirish ---
    elif data == "check_subscription":
        lang_code = get_user_lang(context)
        msg = MESSAGES.get(lang_code, MESSAGES['uz'])
        
        if await is_subscribed(user_id, context):
            await query.edit_message_text(msg['sub_success']) # <--- Tilga mos muvaffaqiyat xabari
        else:
            # Xatolikni ko'rsatish
            error_message = f"{msg['sub_failed_title']} {msg['sub_failed_body']}"
            await query.edit_message_text(error_message) # <--- Tilga mos xato xabari
            
            # Qayta obuna qilish tugmasini ko'rsatish
            await subscription_check_message(query, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchining matnli xabarini qabul qiladi va AI orqali javob beradi."""
    user_id = update.message.from_user.id
    lang_code = get_user_lang(context)
    msg = MESSAGES.get(lang_code, MESSAGES['uz'])
    
    # 1. Obunani har doim tekshirish
    if not await is_subscribed(user_id, context):
        await subscription_check_message(update, context)
        return
        
    # 2. AI dan javob berish
    user_prompt = update.message.text
    
    if not model_status or not client:
        await update.message.reply_text(msg['ai_down'])
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Faqat foydalanuvchi so'rovini yuboramiz. Gemini o'zi tilni aniqlab javob beradi.
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=user_prompt 
        )
        await update.message.reply_text(response.text)
        
    except APIError:
        await update.message.reply_text(msg['ai_error'])
    except Exception:
        await update.message.reply_text(msg['unknown_error'])


# ========================================================================
# 5. Asosiy Funksiya (Botni WebHook rejimida ishga tushirish)
# ========================================================================

def main() -> None:
    """Botni server uchun Webhook rejimida yoki lokal Polling rejimida ishga tushiradi."""
    
    # Render uchun muhit o'zgaruvchilarini olish
    PORT = int(os.environ.get('PORT', 8080))
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL:
        # Serverda Webhook rejimida ishga tushirish
        print(f"Webhook rejimida ishga tushirildi: {WEBHOOK_URL}:{PORT}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        # Lokal sinash uchun Polling rejimida ishga tushirish
        print("Lokal Polling rejimida ishga tushirildi...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    # Render'dan PORT qiymatini olish
    port = int(os.environ.get('PORT', 5000)) 

    # Flask ilovasini olingan PORTda ishga tushirish
    app.run(host='0.0.0.0', port=port)