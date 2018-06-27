"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : 
"""
# -*- coding: utf-8 -*-
import sys
import argparse
import json
import websocket
from pycots.common.messaging import Message
from pycots.gateway.settings import WS_GATEWAY_HOST, WS_GATEWAY_PORT


def init_node(ws):
    """
    Send initial node information
    """
    ws.send(json.dumps({
        'type': 'update',
        'data': {'node': 'fd00:aaaa:bbbb::1', 'name': 'websocket', 'led': '0', 'os': 'riot'}
    }))

def main(args):
    """
    Main function.
    """
    try:
        ws = websocket.create_connection(
            "ws://{}:{}/node".format(args.gateway_host,args.gateway_port)
        )
    except ConnectionRefusedError:
        print("Cannot connect to ws://{}:{}".format(args.gateway_host, args.gateway_port))
        return

    init_node(ws)
    while True:
        try:
            msg = ws.recv()
        except:
            print("Connection closed")
            break
        else:
            print(msg)
            if msg == Message.discover_node():
                init_node(ws)
            else:
                msg = json.loads(msg)
                if msg['payload'] == '1':
                    ws.send(
                        json.dumps({'type': 'update','data': {'led': '1'}})
                    )
                else:
                    ws.send(
                        json.dumps({'type': 'update', 'data': {'led': '0'}})
                    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test Websocket node")
    parser.add_argument(
        '--gateway_host', type=str, default=WS_GATEWAY_HOST, help="Gateway Websocket server host."
    )
    parser.add_argument(
        '--gateway_port', type=str, default=WS_GATEWAY_PORT, help="Gateway Websocket server port."
    )
    args = parser.parse_args()
    print(args)
    try:
        main(args)
    except KeyboardInterrupt:
        print("Exiting")
        sys.exit()
