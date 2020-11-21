import os
import dotenv
from telethon import TelegramClient, events
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
from requests.exceptions import (ConnectionError, HTTPError)
import logging

# setting up logger with output to console/file

log = logging.getLogger('check_availability')
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG) 

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

log.addHandler(ch)

def get_env(name):
    return os.environ[name]

dotenv.load_dotenv(dotenv.find_dotenv())

book_list = []
book_index = 0 
BOOKLIST_XML = 'booklist.xml'

def load_booklist():
    if not Path(BOOKLIST_XML).is_file():
        log.debug(f'{BOOKLIST_XML} not found')
        if not download_xml():
            log.critical(f'failed to download xml file')
            return  


    tree = ET.parse(BOOKLIST_XML)
    root = tree.getroot()
    reviews = root.find('reviews')
    for review in reviews.findall('review'):
        book = review.find('book')
        title = book.find('title').text
        description = book.find('description').text
        image_url = book.find('image_url').text
        authors = book.find('authors')
        authors_string = '; '.join([author.find('name').text for author in authors.findall('author')])
        book_list.append((title, description, image_url, authors_string))


def download_xml():
    try:
        r = requests.request("GET", get_env('GOODREADS_URL'), params = {'v':'2', 'id':get_env('GOODREADS_USER'), 'key':get_env('GOODREADS_KEY')})
        r.raise_for_status()
        with open(BOOKLIST_XML, 'w') as f:
            f.write(r.text)
        return True
    except ConnectionError as e:
        log.debug(f'failed to connect to {GOODREADS_URL}') 
        return False 
    except HTTPError as e:
        log.debug(f' server error') 
        return False


def next_book():
    global book_index
    if len(book_list) == 0:
        log.debug(f'Empty list returned')
        return None 
    result_book = book_list[book_index]
    book_index = book_index + 1
    if book_index >= len(book_list):
        book_index = 0
    return result_book


bot = TelegramClient(
    os.environ.get('TG_SESSION', 'my_bot'), 
    get_env('TG_API_ID'), 
    get_env('TG_API_HASH')).start(bot_token=get_env('TG_TOKEN'))

@bot.on(events.NewMessage(pattern='/next'))
async def start(event):
    """Send a message when the command /start is issued."""
    
    result_book = next_book()
    if result_book is not None:
        response = f' Твоя книга \n\n{result_book[3]} \n\n{result_book[0]} \n\n{result_book[1]} \n\n<a href="{result_book[2]}">&#8205;</a>'
        await event.respond(response, parse_mode='html')
    else:
        await event.respond('Рекомендаций нет') 
    raise events.StopPropagation

def main():
    """Start the bot."""
    load_booklist()
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()