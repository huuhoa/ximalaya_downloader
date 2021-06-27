#!/usr/bin/env python3


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/77.0.3865.120 Safari/537.36'


def get_hex_digest(value: str) -> str:
    import hashlib
    m = hashlib.sha256()
    m.update(value.encode())
    return m.hexdigest()


def save_url_to_cache(url):
    """
    * performs GET to URL and save content (text) to cache folder
    * don't perform GET if cache content is already existed

    Prerequisite:
    * need cache folder to be created first
    """
    import requests
    import os

    url_hash = get_hex_digest(url)

    cache_path = os.path.join('.cache', url_hash)
    if os.path.isfile(cache_path):
        return cache_path

    temp_path = os.path.join('.cache', f'{url_hash}.temp')
    headers = {"User-Agent": USER_AGENT}
    with open(temp_path, "wb") as file:
        # get request
        response = requests.get(url, headers=headers)
        # write to file
        file.write(response.content)

    os.rename(temp_path, cache_path)
    return cache_path


def parse_html(path):
    with open(path, 'r') as file:
        html_doc = file.read()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    title = soup.select_one('h1.title').contents[0]
    # title = soup.select_one('h1.title._II0L').contents[0]
    result = {
        'title': title,
        'list': []
    }
    for div in soup.select('div.sound-list._BJ'):
        for d in div.select('div.text.VN_'):
            href = d.a['href']
            track_id = href.split("/")[-1]
            track_url = 'https://www.ximalaya.com/tracks/%s.json' % track_id
            result['list'].append((href, track_url, track_id))

    return result


def download_media_file(url, file_name):
    import os
    import pycurl

    if os.path.isfile(file_name):
        print(f'already downloaded: {file_name}')
        return

    # open in binary mode
    print(f'start download: {file_name}')
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.USERAGENT, USER_AGENT)
    # c.setopt(c.VERBOSE, True)

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
    print(f'download done: {file_name}')


def parse_track_json(path):
    import json
    import re
    import os

    with open(path, 'r') as file:
        json_data = file.read()

    js = json.loads(json_data)
    play_path_64 = js['play_path_64']
    title = js['title']
    title = re.sub(r'[^\x00-\x7f]', r'', title)
    _, file_extension = os.path.splitext(play_path_64)
    file_name = '%s%s' % (title, file_extension)
    return play_path_64, file_name


def convert_media_file(file_name, extension):
    r"""
    Convert existing media file to another format using ffmpeg
    :param file_name: full path to existing media file
    :param extension: new format
    :return:
    """
    import os
    import subprocess

    root, _ = os.path.splitext(file_name)
    final_file_name = f'{root}.{extension}'
    print(f'converting to: {final_file_name}')
    subprocess.run(['ffmpeg', '-i', file_name, '-y', '-acodec', 'libmp3lame', '-aq', '4', final_file_name],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    print(f'converting done: {final_file_name}')
    # another approach to use ffmpeg-python
    # import ffmpeg
    #
    # (
    #     ffmpeg
    #     .input(file_name)
    #     .output(filename=f'{root}.{extension}', acodec='libmp3lame', aq=4)
    #     .run()
    # )


def download_track(album_path, naming, extension, track_info):
    import os

    href, track_url, track_id = track_info
    track_path = save_url_to_cache(track_url)
    play_path, track_file_name = parse_track_json(track_path)
    has_error = False
    try:
        file_name = os.path.join(album_path, track_file_name)
        if naming == 'track':
            file_name = os.path.join(album_path, f'{track_id}_{track_file_name}')
        download_media_file(play_path, file_name)
        _, ext = os.path.splitext(file_name)
        if ext != f'.{extension}':
            convert_media_file(file_name, extension)
    except Exception as ex:
        print(ex)
        has_error = True
        pass

    return has_error


def main():
    import os
    import argparse
    from concurrent.futures import ThreadPoolExecutor
    from functools import partial

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="album url", type=str)
    parser.add_argument('--naming', help='naming scheme for output file. '
                                         'Default: will use default filename from URL. '
                                         'Track: will append track_id to the final filename',
                        type=str, default='default',
                        choices=['default', 'track'])
    parser.add_argument('--extension', '-e', help='file name extension', type=str, default='m4a',
                        choices=['m4a', 'mp3'])
    args = parser.parse_args()

    os.makedirs('.cache', exist_ok=True)
    url = args.url
    path = save_url_to_cache(url)
    result = parse_html(path)

    album_title = result['title']
    print('album name: %s' % album_title)
    album_path = os.path.join('./downloads', album_title)
    os.makedirs(album_path, exist_ok=True)

    has_error = False
    with ThreadPoolExecutor(max_workers=10) as executor:
        func = partial(download_track, album_path, args.naming, args.extension)
        errors = executor.map(func, [r for r in result['list']])
        for err in errors:
            if err:
                has_error = True

    if has_error:
        print('download is done however there are some errors occur. Please rerun the download command to retry!')
    else:
        print('album %s is downloaded' % result['title'])


if __name__ == '__main__':
    main()
