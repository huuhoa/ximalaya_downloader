# Download tracks from Ximalaya

## Prerequisite

```bash
$ pip3 install requests beautifulsoup4 pycurl
```

## Usage

```bash
$ python3 main.py [album_url]
```

Example: to download **"Harvard Business Lessons"** at url `https://www.ximalaya.com/waiyu/11692226/`

```bash
$ python3 main.py https://www.ximalaya.com/waiyu/11692226/
```

## Troubleshooting

Sometime, server disconnects client, maybe, to prevent automate downloaders. The error message is something like

```bash
* Recv failure: Connection reset by peer
* Closing connection 0
Traceback (most recent call last):
  File "main.py", line 142, in <module>
  File "main.py", line 138, in main
  File "main.py", line 89, in download_file
pycurl.error: (56, 'Recv failure: Connection reset by peer')
```

All we have to do is wait for sometime - for cooldown - and rerun the download command. The waiting time maybe a few seconds to few minutes.
