#!/usr/bin/python3
"""
DevEUI batch registration tool
"""

import random
import logging
import sys
import concurrent.futures
import urllib.request
import argparse
import json

FORMAT = '%(asctime)s %(levelname)s - %(message)s'
logging.basicConfig(filename="%s.log" % sys.argv[0], level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('devEUI_reg')

def remote_HTTP_registration(devEUI, registration_api, timeout):
    """
    Specific Registration function over HTTP.
    This function can be overridden with a mock in unit tests.
    :param devEUI: the id to be registered
    :param registration_api: the URL of the registration function
    :param timeout:
    :return: True if the registration was successful, False for ID conflict; raises Exception for errors.
    """
    url = registration_api if registration_api.startswith('http:') else ("http://%s" % registration_api)
    data = str(json.dumps({'deveui': devEUI})).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        if resp.status == 200:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 422:
            log.debug("422 devEUI has already been used: %s" % (devEUI))
            return False

def get_short_code(devEUI):
    """
    :param devEUI: 16-digit hexa devEUI
    :return: 5-digit short code
    """
    return devEUI[-5:]

class BatchRegistration():
    """
    DevEUI batch registration class
    """
    def __init__(self, args):
        ""
        self.args = args
        self.total_timeout = args.timeout * args.batch_size / args.num_workers
        log.debug("total_timeout: %s" % self.total_timeout)
        self.short_codes_used = set()
        self.registered_ids = set()
        random.seed()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers)
        self.remote_registration_function = remote_HTTP_registration
        self.progress_bar_enabled = not args.verbose

    def generate_unique_devEUI(self):
        """
        :return: a random ID whose 5-char short code is unique
        """
        while True:
            devEUI = "{0:0{1}X}".format(random.randrange(16**16), 16)
            short_code = get_short_code(devEUI)
            if not get_short_code(devEUI) in self.short_codes_used:
                self.short_codes_used.add(short_code)
                return devEUI

    def register_task(self, n):
        """
        Generic registration logic: generate a random devEUI, try to register, and if the remote_registration_function
        indicates that the id was already used then retry with another random id.
        This level of abstraction was made so that things can be unit tested with a mock function instead of a real
        remote function using HTTP.
        :param n:
        :return:
        """
        max_attempts = 10
        try:
            for attempt in range(max_attempts):
                id = self.generate_unique_devEUI()
                log.debug("    - Registering %s (%s/%s) ..." % (id, n, attempt))
                remote_fn = self.remote_registration_function
                success = remote_fn(devEUI=id, registration_api=self.args.registration_api, timeout=self.args.timeout)
                if success:
                    self.registered_ids.add(id)
                    log.debug(" OK - Successfully registered: %s (%s)" % (id, n))
                    self.progress_bar()
                    return id
                else:
                    log.debug("NOK - devEUI has already been used: %s (%s)" % (id, n))
                    continue
        except:
            log.exception("Unexpected exception")
            self.executor.shutdown()
            return None

    def progress_bar(self):
        if self.progress_bar_enabled:
            sys.stderr.write('.')
            sys.stderr.flush()

    def do_batch(self):
        """
        Register a batch of devEUIs
        :return:
        """
        #with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_workers) as executor:
        with self.executor:
            try:
                for id in self.executor.map(self.register_task, range(self.args.batch_size), timeout=self.total_timeout):
                    pass
            except KeyboardInterrupt:
                sys.stderr.write("\nSIGINT detected... please wait for in-flight requests to finish (request timeout=%d s)...\n" % args.timeout)
                self.executor.shutdown()

        return list(self.registered_ids)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DevEUI batch registration tool and HTTP API daemon')
    parser.add_argument('registration_api', help='URL of the devEUI registration API')
    parser.add_argument('--batch', dest='batch_size', help='The batch size of DevEUIs to be registered (default 100)', type=int, default=100)
    parser.add_argument('--timeout', dest='timeout', help='Timeout per registration request (default 10)', type=int, default=10)
    parser.add_argument('--workers', dest='num_workers', help='Number of parallel requests in-flight (default 10)', type=int, default=10, choices=range(1, 11))
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print debug-level information on screen')
    args = parser.parse_args()

    sh = logging.StreamHandler(sys.stderr)
    if args.verbose:
        sh.setLevel(logging.DEBUG)
    else:
        sh.setLevel(logging.INFO)
    log.addHandler(sh)

    log.debug("Starting registration batch...")
    result = BatchRegistration(args).do_batch()

    print("\nShort Code\tDevEUI")
    for devEUI in result:
        print("{:10}\t{}".format(get_short_code(devEUI), devEUI))
    print("\n%s devEUIs total" % len(result))
