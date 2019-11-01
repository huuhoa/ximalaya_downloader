#!/usr/bin/env python3

'''
* performs GET to URL and save content (text) to cache folder
* don't perform GET if cache content is already existed

Prerequisite:
* need cache folder to be created first
'''
def download_html(url):
    import requests
    import hashlib
    import os

    m = hashlib.sha256()
    m.update(url.encode())
    url_hash = m.hexdigest()

    cache_path = os.path.join('.cache', url_hash)
    if os.path.isfile(cache_path):
        return cache_path

    temp_path = os.path.join('.cache', '%s.temp' % url_hash)
    headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"}
    with open(temp_path, "wb") as file:
        # get request
        response = requests.get(url, headers=headers)
        # write to file
        file.write(response.content)

    os.rename(temp_path, cache_path)
    return cache_path


def parse_html(path):
    import urllib.parse

    with open(path, 'r') as file:
        html_doc = file.read()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    title = soup.select_one('h1.title._II0L').contents[0]
    result = {
        'title': title,
        'list': []
    }
    for div in soup.select('div.sound-list._c2'):
        for d in div.select('div.text._c2'):
            href = d.a['href']
            track_id = href.split("/")[-1]
            track_url = 'https://www.ximalaya.com/tracks/%s.json' % track_id
            result['list'].append((href, track_url))

    return result


def download_file(url, file_name):
    import requests
    import os
    import pycurl

    if os.path.isfile(file_name):
        print('already downloaded %s' % file_name)
        return

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Referer': url,
    }

    # open in binary mode
    print('start download: %s' % file_name)
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.USERAGENT, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36')
    #c.setopt(c.VERBOSE, True)
    
    temp_file = '%s.temp' % file_name
    # Setup writing
    if os.path.exists(temp_file):
        f = open(temp_file, "ab")
        c.setopt(pycurl.RESUME_FROM, os.path.getsize(temp_file))
    else:
        f = open(temp_file, "wb")

    c.setopt(c.WRITEDATA, f)
    try:
        c.perform()        
    finally:
        c.close()
        f.close()

    os.rename(temp_file, file_name)
    print('download done')


def parse_track_json(path):
    import json
    import re
    import os

    with open(path, 'r') as file:
        jsdata = file.read()

    js = json.loads(jsdata)
    play_path_64 = js['play_path_64']
    title = js['title']
    title = re.sub(r'[^\x00-\x7f]',r'', title)
    _, file_extension = os.path.splitext(play_path_64)
    file_name = '%s%s' % (title, file_extension)
    return play_path_64, file_name


def download_track(album_path, track_url):
    import os

    track_path = download_html(track_url)
    play_path, track_file_name = parse_track_json(track_path)
    track_file_name = os.path.join(album_path, track_file_name)

    has_error = False
    try:
        download_file(play_path, track_file_name)
    except Exception as ex:
        print(ex)
        has_error = True
        pass

    return has_error


def main():
    import os
    import argparse
    import concurrent
    from concurrent.futures import ThreadPoolExecutor
    from functools import partial

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="album url", type=str)
    args = parser.parse_args()

    os.makedirs('.cache', exist_ok=True)
    url = args.url
    path = download_html(url)
    result = parse_html(path)

    album_title = result['title']
    print('album name: %s' % album_title)
    album_path = os.join('./downloads', album_title)
    os.makedirs(album_path, exist_ok=True)

    has_error = False
    with ThreadPoolExecutor(max_workers=5) as executor:
        func = partial(download_track, album_path)
        errors = executor.map(func, [url for _, url in result['list']])
        for err in errors:
            if err:
                has_error = True

    if has_error:
        print('download is done however there are some errors occur. Please rerun the download command to retry!')
    else:
        print('album %s is downloaded' % result['title'])


if __name__ == '__main__':
    main()

