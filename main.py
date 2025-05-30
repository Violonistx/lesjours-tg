import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import config
from handlers.auth import start_handler, logout_handler, menu_handler
from handlers.masterclasses import classes_handler, masterclass_callback
from handlers.profile import about_handler
from handlers.certificates import certificates_handler, cert_callback_handler
from services.api_client import LesJoursAPI
from handlers.orders import list_orders, order_detail_callback
from handlers.universal_contact import contact_handler

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    app.bot_data['api'] = LesJoursAPI(config.API_BASE_URL)
    app.add_handler(start_handler)
    app.add_handler(logout_handler)
    app.add_handler(classes_handler)
    app.add_handler(CallbackQueryHandler(masterclass_callback, pattern=r'^mc:'))
    app.add_handler(CallbackQueryHandler(order_detail_callback, pattern=r'^order:detail:'))
    app.add_handler(about_handler)
    app.add_handler(certificates_handler)
    app.add_handler(cert_callback_handler)
    app.add_handler(contact_handler)
    app.add_handler(menu_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
