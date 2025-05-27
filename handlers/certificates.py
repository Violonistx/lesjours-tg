from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import logging

user_certificate = {}

async def list_certificates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user_id = str(update.effective_user.id)
    token = api.tokens.get(user_id)
    if not token:
        await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
        return
    try:
        data = api.list_certificates(user_id)
    except Exception as e:
        if 'Требуется авторизация' in str(e):
            await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
            return
        else:
            await update.message.reply_text(f'Ошибка при получении сертификатов: {e}')
            return
    for item in data['results']:
        photo_url = None
        if item.get('image'):
            photo_url = item['image']
        elif item.get('bucket_link') and isinstance(item['bucket_link'], list) and item['bucket_link'][0].get('url'):
            photo_url = item['bucket_link'][0]['url']
        caption = f"{item['title']}\nЦена: {item['price']}₽"
        buttons = [[InlineKeyboardButton(f"Купить", callback_data=f'cert:buy:{item["id"]}')]]
        if photo_url:
            await update.message.reply_photo(photo_url, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(buttons))

async def certificate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, action, value = query.data.split(':', 2)
    cert_id = int(value)
    if action == 'buy':
        user_id = query.from_user.id
        user_certificate[user_id] = cert_id
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton('Отправить номер телефона', request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.reply_text(
            'Пожалуйста, отправьте свой номер телефона для покупки сертификата:',
            reply_markup=reply_markup
        )
        await query.answer()
        return

async def cert_phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user = update.effective_user
    contact = update.message.contact
    if not contact or contact.user_id != user.id:
        await update.message.reply_text('Пожалуйста, используйте кнопку для отправки своего номера телефона.')
        return
    user_id = str(user.id)
    token = api.tokens.get(user_id)
    if not token:
        await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
        return
    cert_id = user_certificate.pop(user_id, None)
    if not cert_id:
        await update.message.reply_text('Не удалось определить сертификат для покупки. Попробуйте ещё раз.')
        return
    try:
        order = api.buy_certificate(user_id, {
            'certificate_id': cert_id,
            'phone': contact.phone_number,
            'telegram_id': user_id,
            'telegram_username': user.username or ''
        })
        await update.message.reply_text(
            f"Вы успешно приобрели сертификат! Детали отправлены на ваш телефон."
        )
    except Exception as e:
        if 'Требуется авторизация' in str(e):
            await update.message.reply_text('Ошибка авторизации! Пожалуйста, нажмите /start для повторной авторизации.')
            return
        await update.message.reply_text(f'Ошибка при покупке сертификата: {e}')
        logging.exception(e)

certificates_handler = CommandHandler('certificates', list_certificates)
cert_callback_handler = CallbackQueryHandler(certificate_callback, pattern=r'^cert:')
cert_phone_handler = MessageHandler(filters.CONTACT, cert_phone_handler)
