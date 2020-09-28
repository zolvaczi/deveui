#!/usr/bin/python3
"""
DevEUI batch registration REST API
"""

import logging
import sys
import argparse
import connexion
import deveui_batch
from flask import current_app
import threading
from queue import Queue
import collections

FORMAT = '%(asctime)s %(name)s %(levelname)s - %(message)s'
logging.basicConfig(filename="%s.log" % sys.argv[0], level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('devEUI_reg')

# TODO: create a global config object in a different module and store your args there!

Message = collections.namedtuple('Message', ['batch_id', 'batch_size'])
QUIT_SIGNAL = Message('QUIT',-1)

def add_batch(body):
    batch_size = body.get('batch_size', 100)
    log.debug("add_batch(%s)" % batch_size)
    with current_app.app_context():
        current_app.request_q.put(Message('1', batch_size))
    return {}, 201, {'Location': 'batch/1'}

def get_batch(batch_id):
    log.debug("get_batch(%s)" % batch_id)
    with current_app.app_context():
        log.debug("ready_batches: %s" % current_app.ready_batches)
        status = "Completed" if batch_id in current_app.ready_batches else "Processing"
        deveuis = current_app.ready_batches.get(batch_id, [])
        body = {'id': batch_id, 'status': status, 'deveuis': deveuis}
        log.debug("body: %s", body)
        return body, 200

def remove_batch(batch_id):
    log.debug("remove_batch(%s)" % batch_id)
    raise NotImplementedError("Removal of a batch is not implemented yet")

def get_all_batches():
    log.debug("get_all_batches")
    raise NotImplementedError("Retrieval of all batches is not implemented yet")

def create_app(request_q, ready_batches):
    app = connexion.App(__name__, specification_dir='openapi/')
    app.add_api('specification.yml')
    with app.app.app_context():
        current_app.request_q=request_q
        current_app.ready_batches=ready_batches
    return app

def deveui_batch_thread_fn(request_q, batch_registrator, ready_batches):
    while True:
        msg = request_q.get()
        log.debug("Processing request: %s" % str(msg))
        if msg == QUIT_SIGNAL:
            log.debug('Quitting deveui_batch_thread_fn')
            return
        ready_batches[msg.batch_id] = batch_registrator.do_batch(msg.batch_size)
        log.debug('Request %s processed: %s' % (msg, ready_batches[msg.batch_id]))

def main():
    global args
    parser = argparse.ArgumentParser(description='DevEUI batch registration tool and HTTP API daemon')
    parser.add_argument('registration_api', help='URL of the devEUI registration API')
    parser.add_argument('--port', dest='port', help='Daemon listen port number (default 8080)', type=int, default=8080)
    parser.add_argument('--timeout', dest='timeout', help='Timeout per registration request (default 15)', type=int, default=15)
    parser.add_argument('--workers', dest='num_workers', help='Number of parallel requests in-flight (default 10)', type=int, default=10, choices=range(1, 11))
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print debug-level information on screen')
    args = parser.parse_args()

    batch_registrator = deveui_batch.BatchRegistration(args)
    request_q = Queue()
    ready_batches = {}
    deveui_batch_thread = threading.Thread(target=deveui_batch_thread_fn, args=(request_q,batch_registrator,ready_batches), daemon=True)
    deveui_batch_thread.start()

    app = create_app(request_q, ready_batches)
    app.run(port=args.port, debug=args.verbose)

    log.debug('Sending shutdown message to batch_registrator')
    request_q.put(QUIT_SIGNAL)
    log.debug('Quitting app')

if __name__ == '__main__':
    main()

