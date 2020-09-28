import pytest
import deveui_batch
import collections
import time

counter = 0
success_counter = 0

def mock_remote_function(devEUI, registration_api, timeout):
    """
    Simulation of the success of remote registration with pseudo-random behaviour: increments and modulo div of primes
    """
    global counter
    global success_counter
    counter += 79
    time.sleep((counter % 3) / 2.0)
    success = counter % 29 < 25
    if success:
        success_counter += 1
    return success

Args = collections.namedtuple('Args',
                              ['registration_api', 'daemon', 'port', 'host', 'batch_size', 'timeout', 'num_workers',
                               'verbose'])

args = Args(registration_api='xyz', daemon=False, port='', host='', batch_size=100,
            timeout=10, num_workers=10, verbose=False)

def test_count():
    db = deveui_batch.BatchRegistration(args)
    db.remote_registration_function = mock_remote_function
    result = db.do_batch(args.batch_size)
    assert len(result)==100
    assert success_counter==100

