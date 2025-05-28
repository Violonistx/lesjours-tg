from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
import logging

from handlers.certificates import list_certificates
from handlers.masterclasses import list_masterclasses

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = context.bot_data['api']
    user = update.effective_user
    contact = update.message.contact
    if not contact or contact.user_id != user.id:
        await update.message.reply_text('Пожалуйста, используйте кнопку для отправки своего номера телефона.')
        return
    awaiting = context.user_data.get('awaiting')
    if awaiting == 'certificate':
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
        context.user_data['awaiting'] = None
        return
    elif awaiting == 'masterclass':
        user_id = user.id
        event_id = context.user_data.get('event_id')
        if not event_id:
            await update.message.reply_text('Не удалось определить мастер-класс для бронирования. Попробуйте ещё раз.')
            return
        api_user_id = api.get_api_user_id(user_id)
        if not api_user_id:
            await update.message.reply_text('Ошибка: не удалось определить пользователя на сервере. Попробуйте /start.')
            return
        try:
            api.add_to_cart(user_id, api_user_id, event_id, guests_amount=1)
            checkout_data = {
                'phone': contact.phone_number,
                'telegram_id': user_id,
                'telegram_username': user.username or ''
            }
            api.checkout(user_id, api_user_id, checkout_data)
            await update.message.reply_text(
                "Вы успешно записались на мастер-класс! Заказ оформлен, с вами свяжется менеджер для подтверждения.\n\nЕсли возникли вопросы, напишите нашему менеджеру: @les_jour_mk",
                reply_markup=ReplyKeyboardMarkup([
                    ['В главное меню']
                ], resize_keyboard=True)
            )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            err_text = ''
            import requests
            if isinstance(e, requests.HTTPError) and hasattr(e, 'response'):
                err_text = e.response.text
                await update.message.reply_text(f'Ошибка при бронировании (HTTP): {e.response.status_code}\n{err_text}')
            else:
                err_text = str(e)
                await update.message.reply_text(f'Ошибка при бронировании (Exception): {err_text}')
            await update.message.reply_text(f'Traceback:\n{tb}')
        context.user_data['awaiting'] = None
        return
    else:
        await update.message.reply_text('Не удалось определить действие. Попробуйте ещё раз.')

contact_handler = MessageHandler(filters.CONTACT, contact_handler) 