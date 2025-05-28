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
            await query.message.reply_text(
                'Пожалуйста, отправьте свой номер телефона для покупки сертификата:',
                reply_markup=reply_markup
            )
            await query.answer()
        except Exception as e:
            await query.message.reply_text(f'Ошибка при добавлении сертификата в корзину: {e}')
            return
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
    cert_id = context.user_data.get('cert_id')
    price = context.user_data.get('cert_price')
    api_user_id = api.get_api_user_id(user_id)
    if cert_id is None or price is None or not api_user_id:
        await update.message.reply_text('Не удалось определить сертификат для покупки. Попробуйте ещё раз.')
        return
    try:
        # Чекаут
        order = api.checkout(user_id, api_user_id, {
            'amount': price,
            'phone': contact.phone_number,
            'telegram_id': user_id,
            'telegram_username': user.username or ''
        })
        await update.message.reply_text(
            f"Вы оформили сертификат на сумму {price} ₽. Для уточнения деталей свяжитесь с менеджером.",
            reply_markup=ReplyKeyboardMarkup([
                ['В главное меню'],
                ['Связаться с менеджером']
            ], resize_keyboard=True)
        )
    except Exception as e:
        await update.message.reply_text(f'Ошибка при покупке сертификата: {e}')
        logging.exception(e)

certificates_handler = CommandHandler('certificates', list_certificates)
cert_callback_handler = CallbackQueryHandler(certificate_callback, pattern=r'^cert:')
cert_phone_handler = MessageHandler(filters.CONTACT, cert_phone_handler)
