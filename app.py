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
        url = url_for('pic')
    return url

def get_pic_from_hipchat():
    url = None
    try:
        # get last messages
        r = requests.get("http://api.hipchat.com/v2/room/{}/history/latest".format(room_id), params=auth_params)

        # if there is no 'items' key then something went wrong
        if not 'items' in r.json().keys():
            print "Check your API token"
            return None

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

        cache.set('pic_url', url)

    except Exception:
        return None

    return url

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/get_last_pic_url")
def last_pic_url():
    url = get_pic_from_hipchat()
    if url is None:
        url = get_cached_url()
    return jsonify({'url': url})

@app.route("/default_pic")
def pic():
    return app.send_static_file('default_pic.png')

if __name__ == "__main__":
    app.run(debug=False)
