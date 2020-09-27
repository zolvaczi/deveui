#!/usr/bin/python3
"""
DevEUI batch registration REST API
"""

import logging
import sys
import argparse

FORMAT = '%(asctime)s %(levelname)s - %(message)s'
logging.basicConfig(filename="%s.log" % sys.argv[0], level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('devEUI_reg')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DevEUI batch registration tool and HTTP API daemon')
    parser.add_argument('registration_api', help='URL of the devEUI registration API')
    parser.add_argument('--daemon', dest='daemon', action='store_true', help='Run as a daemon')
    parser.add_argument('--port', dest='port', help='Daemon listen port number (default 8080)', type=int, default=8080)
    parser.add_argument('--host', dest='host', help='Daemon host', default='localhost')
    parser.add_argument('--batch', dest='batch_size', help='The batch size of DevEUIs to be registered (default 100)', type=int, default=100)
    parser.add_argument('--timeout', dest='timeout', help='Timeout per registration request (default 10)', type=int, default=10)
    parser.add_argument('--workers', dest='num_workers', help='Number of parallel requests in-flight (default 10)', type=int, default=10, choices=range(1, 11))
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print debug-level information on screen')
    args = parser.parse_args()

    #result = BatchRegistration(args).do_batch()
