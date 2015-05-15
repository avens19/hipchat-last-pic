import json
from time import sleep

import requests

from settings import token, room_id


auth_params = {'auth_token': token}
giphy_api_key = 'dc6zaTOxFJmzC'


def translate_to_gif():
    # get last messages
    r = requests.get("http://api.hipchat.com/v2/room/{}/history/latest".format(room_id), params=auth_params)

    # if there is no 'items' key then something went wrong
    if 'items' not in r.json().keys():
        return

    # find last image url
    message = r.json()['items'][-1]
    if message.get('message_links', None) or message.get('file', None):
        pass
    else:
        try:
            data = {}
            data['s'] = message['message']
            data['api_key'] = giphy_api_key
            r = requests.get("http://api.giphy.com/v1/gifs/translate", params=data)
            url = r.json()['data']['images']['original']['url']

            r = requests.post("http://api.hipchat.com/v2/room/{}/message".format(room_id), params=auth_params, data=json.dumps({'message': url}))
            print url
        except:
            pass

if __name__ == "__main__":
    while True:
        translate_to_gif()
        sleep(5)
