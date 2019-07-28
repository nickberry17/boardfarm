# Copyright (c) 2015
#
# All rights reserved.
#
# This file is distributed under the Clear BSD license.
# The full text can be found in LICENSE in the root directory.
#!/usr/bin/env python

import platform
import os
import re
import socket
import sys

import requests

class BoardfarmWebClient(object):
    '''
    Handles interacting with a boardfarm server. For checking out
    stations, etc.
    '''

    def __init__(self, config_url, bf_version="1.0.0", debug=False):
        self.config_url = config_url
        self.bf_version = bf_version
        self.debug = debug
        self.server_url = None
        self.server_version = None
        self.checked_out = None
        # If config isn't on a server, do nothing
        if not config_url.startswith('http'):
            return
        self.headers = {'user-agent': self._user_agent()}
        self.default_data = {'hostname': socket.gethostname(),
                             'username': os.environ.get('BUILD_USER_ID', None) or \
                                         os.environ.get('USER', None),
                             'build_url': os.environ.get('BUILD_URL', None)
                            }
        try:
            # See if this is a boardfarm server by checking the root /api path
            self.server_url = re.search('http.*/api', self.config_url).group(0)
            r = requests.get(self.server_url, headers=self.headers)
            data = r.json()
            self.server_version = data.get('version', None)
            print("Using %s as boardfarm server, version %s" %
                  (self.server_url, self.server_version))
        except Exception as e:
            if self.debug:
                print(e)
                print("The server hosting '%s' does not appear to be a "
                      "boardfarm server." % self.config_url)

    def _user_agent(self):
        bfversion = 'Boardfarm %s' % self.bf_version
        s = platform.system()
        py = "Python %s.%s.%s" % (sys.version_info[:3])
        try:
            system = platform.system()
            if system == 'Linux':
                s = "%s %s" % platform.linux_distribution()[:2]
            elif system == 'Darwin':
                s = "MacOS %s" % platform.mac_ver()[0]
            elif system == 'Windows':
                s = "Windows %s" % platform.win32_ver()[0]
        except Exception as e:
            if self.debug:
                print('Unable to get more specific system info')
        return ";".join([bfversion, py, s])

    def post_note(self, name, note):
        '''
        If an error is encountered with a station, use this function
        to send a message to the boardfarm server. Something short
        and useful for display.
        '''
        if not self.server_version:
            return
        try:
            url = self.server_url + "/stations/" + name
            requests.post(url, json={"note": note}, headers=self.headers)
        except Exception as e:
            if self.debug:
                print(e)
                print("Failed to notify boardfarm server with message.")

    def checkout(self, config):
        if not self.server_version:
            return
        try:
            # Gather all the '_id' keys out of the config
            station_id = config.get('_id', None)
            device_ids = []
            if "devices" in config:
                device_ids = [x["_id"] for x in config["devices"] if "_id" in x]
            self.checked_out = {"ids": [station_id] + device_ids,
                                "name": config.get("station", None)}
            self.checked_out.update(self.default_data)
            url = self.server_url + "/checkout"
            requests.post(url, json=self.checked_out, headers=self.headers)
            print("Notified boardfarm server of checkout")
            if self.debug:
                print(self.checked_out)
        except Exception as e:
            if self.debug:
                print(e)
                print("Failed to notify boardfarm server of checkout")

    def checkin(self):
        if not self.server_version or not self.checked_out:
            return
        try:
            url = self.server_url + "/checkin"
            requests.post(url, json=self.checked_out, headers=self.headers)
            print("Notified boardfarm server of checkin")
            if self.debug:
                print(self.checked_out)
        except Exception as e:
            if self.debug:
                print(e)
                print("Failed to notify boardfarm server of checkin")

if __name__ == '__main__':
    bf_config = "http://boardfarm.myexamplesite.com/api/bf_config"
    #bf_config = "../bf_config.json"
    bfweb = BoardfarmWebClient(bf_config, debug=False)
    bfweb.checkout({"_id": "1111",
                    "station": "rpi3",
                    "devices": [{"_id": "1112"}]})
    bfweb.checkin()