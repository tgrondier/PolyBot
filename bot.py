#!/usr/bin/env python3

import logging

import requests
from booru import Booru
from configobj import ConfigObj
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram.ext.dispatcher import run_async

from settings import AKARIN_TOKEN, OWNER_ID, SHUTDOWN_IMAGE, TELEGRAM_TOKEN, MANDATORY_TAGS, IGNORED_TAGS, BOORU

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

br = Booru("safebooru.org", mandatory_tags=MANDATORY_TAGS, ignored_tags=IGNORED_TAGS)
sb = br.request_manager


sleeping = False


def log(fn):
    def wrapper(bot, update, *args, **kwargs):
        logging.info(f"Received update: {update}")
        return fn(bot, update, *args, **kwargs)

    return wrapper


def check_permissions(admin_only=False):

    def decorator(fn):

        @log
        def wrapper(bot, update, *args, **kwargs):

            if update.message.from_user.id == OWNER_ID:
                return fn(bot, update, *args, **kwargs)

            if not admin_only and not sleeping:
                return fn(bot, update, *args, **kwargs)

            return lambda x: x
        return wrapper

    return decorator


def start(bot, update):
    help(bot, update)
    pass


@check_permissions()
def help(bot, update):
    """ Answer in Telegram """

    text = "/safebooru - Gets a random image corresponding to the tags from safebooru. rating:safe tag enforced. " \
           "Takes at least one argument.\n" \
           "/sb - safebooru alias\n" \
           "/catgirl - Same as /safebooru, but searches for catgirls specificaly. arguments are optional.\n" \
           "/taglist - Returns a link to the safebooru taglist. Arguments are ignored\n" \
           "/akarin - URL shortener; return a shortened link of the argument. Accepts custom url as second " \
           "argument\n" \
           "/waaai - akarin alias\n" \
           "/anilist - Anilist search"

    bot.sendMessage(update.message.chat_id, text=text, disable_web_page_preview=True)


@run_async
@check_permissions()
def akarin(bot, update, args):

    if len(args) < 1:
        bot.sendMessage(update.message.chat_id, text='わあああいーあかりんパラメータを見つけられなかった　( ≧Д≦)',
                        reply_to_message_id=update.message.message_id)
        return

    payload = {
        'key': AKARIN_TOKEN,
        'url': args[0]
    }

    if len(args) > 1:
        payload['custom'] = args[1]

    r = requests.get('https://api.waa.ai/shorten', params=payload).json()

    if r['success']:
        bot.sendMessage(update.message.chat_id, text=r['data']['url'], disable_web_page_preview=True,
                        reply_to_message_id=update.message.message_id)

    else:
        bot.sendMessage(update.message.chat_id, text="”" + r['data']['error'] + '”？ えー　なにそれ、あかりんいみわかんあい ヾ( •́д•̀ ;)ﾉ',
                        reply_to_message_id=update.message.message_id)


@run_async
@check_permissions()
def safebooru(bot, update, args):
    if len(args) < 1:
        bot.sendMessage(update.message.chat_id, text='There are no arguments, b-baka !',
                        reply_to_message_id=update.message.message_id)

    tags = " ".join(args)

    image = sb.random(tags=tags)

    url = br.generate_image_url(image)

    update.message.reply_photo(url, reply_to_message_id=update.message.message_id)


@run_async
def catgirl(bot, update, args):
    args.append("cat_ears")
    safebooru(bot, update, args)


@check_permissions(admin_only=True)
def wakeup(bot, update):
    logging.info("Waking up PolyBot")
    sleeping = True


@check_permissions(admin_only=True)
def goodnight(bot, update):
    logging.info("Putting PolyBot to sleep")
    sleeping = False


def main():

    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(CommandHandler("akarin", akarin, pass_args=True))
    dp.add_handler(CommandHandler("waaai", akarin, pass_args=True))

    dp.add_handler(CommandHandler("safebooru", safebooru, pass_args=True))
    dp.add_handler(CommandHandler("sb", safebooru, pass_args=True))

    dp.add_handler(CommandHandler("catgirl", catgirl, pass_args=True))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
