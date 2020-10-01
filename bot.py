import requests
import json
import urllib.parse

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent

import messages
from tokens import TOKEN_API_BITLY, TOKEN_BOT

BOT_NAME = "@AccorciaLinkBot"
link2shortlink = dict()

def is_url(url):
    '''It checks if the string has the URL format.'''
    try:
        scheme = urllib.parse.urlparse(url).scheme
        return scheme != ""
    except:
        return False

def url_ok(url):
    '''It checks if the link the url brings to is up.'''
    try:
        r = requests.head(url)
        return r.status_code == 200
    except:
        return False

def get_short_link(link, lang):
    if not is_url(link) or not url_ok(link):
        return messages.INVALID_URL_MESSAGE[lang]
    
    # if link has been already shortened, return the shortened link
    if link in link2shortlink.keys():
        return link2shortlink[link]

    # shorting link
    headers = {
        'Authorization': 'Bearer {}'.format(TOKEN_API_BITLY),
        'Content-Type': 'application/json',
    }
    
    data = '{ "long_url": "' + link + '", "domain": "bit.ly" }'
    
    try:
        response = requests.post('https://api-ssl.bitly.com/v4/shorten', headers=headers, data=data)
        result = json.loads(response.text)
        link2shortlink[link] = result["link"]
        return link2shortlink[link]
    except:
        return messages.GENERIC_ERROR_MESSAGE[lang]
    
def get_lang(update, is_query=False):
    '''Function that returns language of user from update (default: en).'''
    if is_query:
        lang = update.inline_query.from_user.language_code
    else:
        lang = update.message.from_user.language_code
    if lang==messages.IT:
        return lang
    return messages.EN

def start_command(update, context):
    '''Function for /start command.'''
    update.message.reply_text(messages.WELCOME_MESSAGE[get_lang(update)])
    
def help_command(update, context):
    '''Function for /help command.'''
    update.message.reply_text(messages.HELP_MESSAGE[get_lang(update)].format(BOT_NAME))
    
def short_link(update, context):
    '''Function for any message received.'''
    update.message.reply_text(get_short_link(update.message.text, get_lang(update)))
    
def inlinequery(update, context):
    '''Function that handles the inline query showing the InlineQueryResultArticle'''
    '''with the shortened link if the content of the query is a valid link.'''
    query = update.inline_query.query
    if query=="":
        return
    
    lang = get_lang(update, True)
    shortlink = get_short_link(query, lang)
    if shortlink == messages.GENERIC_ERROR_MESSAGE[lang] or shortlink == messages.INVALID_URL_MESSAGE[lang]:
        update.inline_query.answer(list())
        return
    
    result = [
        InlineQueryResultArticle(
            id=1,
            title=messages.INLINE_TITLE[lang],
            input_message_content= InputTextMessageContent(shortlink),
        )
    ]

    update.inline_query.answer(result)



updater = Updater(TOKEN_BOT, use_context=True)

dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start_command))
dp.add_handler(CommandHandler("help", help_command))
dp.add_handler(InlineQueryHandler(inlinequery))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, short_link))

# Start the Bot
updater.start_polling()
updater.idle()