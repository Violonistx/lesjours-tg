from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config

user_certificate = {}

async def list_certificates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user_id = update.effective_user.id
    data = api.list_certificates(user_id)
    buttons = [
        [InlineKeyboardButton(f"{item['title']} ({item['price']}₽)", callback_data=f'cert:buy:{item["id"]}')]
        for item in data['results']
    ]
    await update.message.reply_text(
        'Доступные сертификаты:',
        reply_markup=InlineKeyboardMarkup(buttons)
    )

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
    user_id = user.id
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
        await update.message.reply_text('Ошибка при покупке сертификата. Попробуйте позже.')

certificates_handler = CommandHandler('certificates', list_certificates)
cert_callback_handler = CallbackQueryHandler(certificate_callback, pattern=r'^cert:')
cert_phone_handler = MessageHandler(filters.CONTACT, cert_phone_handler)
