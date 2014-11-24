import re
import urlparse
import subprocess

import requests
from flask import Flask, render_template, jsonify, abort, url_for
from werkzeug.contrib.cache import SimpleCache

from settings import token, room_id


picture_regexp = re.compile("^(?P<url>(.*[\s/])?([^\s]+\.[A-Za-z0-9]{2,8}/[^\s]+(jpe?g|png|gif)))$", re.IGNORECASE)

auth_params = {'auth_token': token}

app = Flask(__name__, template_folder='', static_folder='')

cache = SimpleCache()


def get_cached_url():
    # look in cache
    url = cache.get('pic_url')
    if url is None:
        try:
            url = get_pic_from_hipchat()
        except Exception:
            url = url_for('pic')
        else:
            cache.set('pic_url', url, timeout=10)
    return url


def get_pic_from_hipchat():
    # get last messages
    r = requests.get("http://api.hipchat.com/v2/room/{}/history/latest".format(room_id), params=auth_params)

    # if there is no 'items' key then something went wrong
    if not 'items' in r.json().keys():
        return abort(502)

    url = None

    # find last image url
    for message in reversed(r.json()['items']):
        if message.get('message_links', None) and message['message_links'][0]['type'] == 'image':
            url = message['message_links'][0]['image']['image']
            break
        elif message.get('file') and message['file'].get('url'):
            result = picture_regexp.match(message['file']['url'])
            if result:
                url = result.group('url')
                break

    if url is None:
        # no messages with pic url in this room
        return abort(404)

    return url


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/get_last_pic_url")
def last_pic_url():
    return jsonify({'url': get_cached_url()})


@app.route("/version")
def version():
    commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
    return jsonify({'version': commit_hash})


@app.route("/default_pic")
def pic():
    return app.send_static_file('default_pic.png')

if __name__ == "__main__":
    app.run(debug=True)
