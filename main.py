import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import config
from handlers.auth import start_command, logout_handler
from handlers.masterclasses import classes_handler, masterclass_callback

def main():
    logging.basicConfig(level=logging.INFO)
    updater = Updater(config.TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(logout_handler)
    dp.add_handler(classes_handler)
    dp.add_handler(CallbackQueryHandler(masterclass_callback, pattern=r'^mc:'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
