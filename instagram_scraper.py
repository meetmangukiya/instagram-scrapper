
import argparse
import csv
import os
import re
import sys
import threading
from typing import Callable, List

import requests
from requests_html import HTMLSession



# Source: http://blog.jstassen.com/2016/03/code-regex-for-instagram-username-and-hashtags/
REGEXES = {
    'hashtag': re.compile('(?:#)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'),
    'username': re.compile('(?:@)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'),
}

# In case Instagram switches it up on us
IMG_XPATH = '//img[@alt]'

def send_scrape_request(insta_url: str, total_count: int=50, existing: set=None, short_circuit: bool=False):
    """
        :param insta_url:
            Instagram url to scrape
        :param total_count:
            Total amount of images to scrape
        :param existing:
            URLs to skip
        :param short_circuit:
            Whether or not to short_circuit total_count loop 
            
    Yields url, captions, hashtags, and mentions for provided insta url
    """
    session = HTMLSession()
    req = session.get(insta_url)

    imgs = set()
    count = 0
    page = 0
    while count < total_count:
        req.html.render(scrolldown=page)
        images = req.html.xpath(IMG_XPATH)  
        page += 1
        for image in images:
            if count >= total_count:
                break
            try:
                url, caption = image.attrs['src'], image.attrs['alt']
            except Exception as e:
                print(e)
            if url in imgs:
                # Short-circuit if user has less photos than the total_count
                if short_circuit:
                    if len(images) < total_count: 
                        total_count = 0
                        break
                continue
            imgs.add(url)
            hashtags = set(REGEXES['hashtag'].findall(caption))
            mentions = set(REGEXES['username'].findall(caption))
            count += 1
            yield url, caption, hashtags, mentions



def scrape_instagram(target: str, total_count: int=50, existing: set=None, mode: str='tags'):
    """
    :param targets:
        List of targets that need to be scraped.
    :param total_count:
        Total number of images to be scraped.
    :param existing:
        URLs to skip
    :param mode
        Two options: 'tags' or 'users'. Determines whether we are scraping users or tags
        
    Builds url and sets short_circuit based on target and then issues request to url
    """
    if mode == 'users':
        short_circuit = True
        url = f'https://www.instagram.com/{target}'
    else:
        short_circuit = False
        url = f'https://www.instagram.com/explore/tags/{target}'

    yield from send_scrape_request(url, total_count=total_count, existing=existing, short_circuit=short_circuit)


def main(tags: List[str], users: List[str], total_count: int=50, should_continue: bool=False):
    """
    :param tags:
        List of tags to be scraped
    :param users:
        List of users to be scraped
    :param total_count:
        total number of images to be scraped
    :param should_continue
        Flag for whether or not we should read from disk and skip existing URLs
        
    Scrapes user and hashtag images from Instagram
    """
    def _single_input_processing(target: str, total_count: int, existing_links: set, start: int, mode: str='tag'):
        os.makedirs(f'data/{target}', exist_ok=True)
        with open(f'data/{target}/data.csv', 'a' if existing_links else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for count, (url, caption, hashtags, mentions) in enumerate(scrape_instagram(
                target, total_count, existing_links, mode), start):

                try:
                    req = requests.get(url)
                    with open(f'data/{target}/{count}.jpg', 'wb') as img:
                        img.write(req.content)
                except:
                    print(f'An error occured while downloading {url}')
                else:
                    file_index = count + 1
                    writer.writerow([
                        f'{file_index}.jpg',
                        url,
                        caption.replace('\n', '\\n'),
                        ', '.join(hashtags),
                        ', '.join(mentions)
                    ])
                    print(f'[{target}] downloaded {url} as {file_index}.jpg in data/{target}')

    targets = {'tags': tags, 'users': users}
    for mode,lists in targets.items():
        for target in lists:
            existing_links = set()
            start = 0

            if os.path.exists(f'data/{target}/data.csv') and should_continue:
                with open(f'data/{target}/data.csv', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for i, row in enumerate(reader):
                        existing_links.add(row[1])
                    start = i + 1
            _single_input_processing(target, total_count, existing_links, start, mode=mode)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', '-u', default=[], nargs='+', help='Users to scrape images from')
    parser.add_argument('--tags', '-t', default=[], nargs='+',
                        help='Tags to scrape images from')
    parser.add_argument('--count', '-c', type=int, default=50,
                        help='Total number of images to scrape for each given '
                             'tag.')
    parser.add_argument('--continue', '-C',
                        default=False, action='store_true', dest='cont',
                        help='See existing data, and do not parse those again, '
                             'and append to the data file, instead of a rewrite')
    args = parser.parse_args()
    
    assert (len(args.tags) >= 1) or (len(args.users) >= 1), "Enter tags or users to scrape! Use --tags or --users option, see help."
    assert args.count, "Enter total number of images to scrape using --count option, see help."
    main(args.tags, args.users, args.count, args.cont)
