import argparse
import csv
import os
import re
from typing import List

import requests
from requests_html import HTMLSession

# Source: http://blog.jstassen.com/2016/03/code-regex-for-instagram-username-and-hashtags/
REGEXES = {
    'hashtag': re.compile('(?:#)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'),
    'username': re.compile('(?:@)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)'),
}


def scrape_instagram_tag(tag: str, total_count: int=50, existing: set=None):
    """
    Scrape and yield recently tagged instagram photos.
    """
    url = f'https://www.instagram.com/explore/tags/{tag}'
    session = HTMLSession()
    req = session.get(url)

    imgs = set(existing)
    count = 0
    page = 0

    while count <= total_count:
        req.html.render(scrolldown=page)
        images = req.html.xpath('//img[@alt]')
        page += 1
        for image in images:
            if count > total_count:
                break
            try:
                url, caption = image.attrs['src'], image.attrs['alt']
            except:
                pass
            else:
                if url in imgs:
                    continue
                imgs.add(url)
                hashtags = set(REGEXES['hashtag'].findall(caption))
                mentions = set(REGEXES['username'].findall(caption))
                count += 1
                yield url, caption, hashtags, mentions


def scrape_instagram(tags: List[str], total_count: int=50, existing: set=None):
    """
    :param tags:
        List of tags that need to be scraped.
    :param total_count:
        Total number of images to be scraped.
    """
    for tag in tags:
        yield from scrape_instagram_tag(tag, total_count)


def main(tags, total_count, should_continue):
    def _single_tag_processing(tag, total_count, existing_links, start):
        os.makedirs(f'data/{tag}', exist_ok=True)
        with open(f'data/{tag}/data.csv', 'a' if existing_links else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for count, (url, caption, hashtags, mentions) in enumerate(scrape_instagram_tag(
                tag, total_count, existing_links), start):

                try:
                    req = requests.get(url)
                    with open(f'data/{tag}/{count}.jpg', 'wb') as img:
                        img.write(req.content)
                except:
                    print(f'An error occured while downloading {url}')
                else:
                    writer.writerow([
                        f'{count}.jpg',
                        url,
                        caption.replace('\n', '\\n'),
                        ', '.join(hashtags),
                        ', '.join(mentions)
                    ])
                    print(f'[{tag}] downloaded {url} as {count}.jpg in data/{tag}')

    for tag in tags:
        existing_links = set()
        start = 0
        if os.path.exists(f'data/{tag}/data.csv') and should_continue:
            with open(f'data/{tag}/data.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for i, row in enumerate(reader):
                    existing_links.add(row[1])
                start = i + 1
        _single_tag_processing(tag, total_count, existing_links, start)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tags', '-t', nargs='+',
                        help='Tags to scrape images from')
    parser.add_argument('--count', '-c', type=int, default=50,
                        help='Total number of images to scrape for each given '
                             'tag.')
    parser.add_argument('--continue', '-C',
                        default=False, action='store_true', dest='cont',
                        help='See existing data, and do not parse those again, '
                             'and append to the data file, instead of a rewrite')
    args = parser.parse_args()
    assert args.tags, "Enter tags to scrape! Use --tags option, see help."
    assert args.count, "Enter total number of images to scrape using --count option, see help."
    main(args.tags, args.count, args.cont)
