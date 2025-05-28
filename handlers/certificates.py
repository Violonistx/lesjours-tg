from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import logging

user_certificate = {}

async def list_certificates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    denominations = [1,2,3,4,5,7,10,15]
    buttons = []
    for d in denominations:
        buttons.append([InlineKeyboardButton(f"Подарочный сертификат на {d} 000 ₽", callback_data=f'cert:nom:{d*1000}')])
    await update.message.reply_text(
        'Выберите номинал сертификата:',
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return

async def certificate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, action, value = query.data.split(':', 2)
    if action == 'nom':
        amount = int(value)
        user_id = str(query.from_user.id)
        api = context.bot_data['api']
        api_user_id = api.get_api_user_id(user_id)
        if not api_user_id:
            await query.message.reply_text('Ошибка: не удалось определить пользователя. Попробуйте /start.')
            return
        try:
            api.add_to_cart_certificate(user_id, api_user_id, amount)
            reply_markup = ReplyKeyboardMarkup(
                [[KeyboardButton('Отправить номер телефона', request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True
            )
            context.user_data['cert_id'] = 0
            context.user_data['cert_price'] = amount
            context.user_data['awaiting'] = 'certificate'
            await query.message.reply_text(
                'Пожалуйста, отправьте свой номер телефона для покупки сертификата:',
                reply_markup=reply_markup
            )
            await query.answer()
        except Exception as e:
            await query.message.reply_text(f'Ошибка при добавлении сертификата в корзину: {e}')
            return
        return

certificates_handler = CommandHandler('certificates', list_certificates)
cert_callback_handler = CallbackQueryHandler(certificate_callback, pattern=r'^cert:')
