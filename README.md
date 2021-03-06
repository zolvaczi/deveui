# DevEUI batch creation coding challenge

## Usage
### CLI
Basic usage:
`./deveui_batch.py LoRaWan_API_URL`

For detailed parameters, see `./deveui_batch.py -h` 

### API
Basic usage:
To start the API application:
`./daemon_deveui_batch.py LoRaWan_API_URL`

To request for a batch of IDs (100 IDs by deafult):
`curl -v -X POST http://localhost:8080/api/v1/batch`

Or to request a batch of 11 IDs, for instance:
`curl -v -X POST -H "Content-Type: application/json" -d '{"batch_size": 11}' http://localhost:8080/api/v1/batch`

To retrive the result:
`curl -v http://localhost:8080/api/v1/batch/1`

For detailed parameters, see `./daemon_deveui_batch.py -h`

## Tool (CLI) Requirements
1. It must register each DevEUI of the batch (of deafult size 100) with the LoRaWAN provider, and must expect and handle DevEUI conflicts
1. DevEUI format is 16 hex characters
1. The 5-character code (last 5 chars of DevEUI) must be unique within a batch
1. DevEUIs must not be wasted, the tool must return every ID that it registers. The tool must handle interrupts (SIGINT) gracefully, and finish the registrations in-flight before exiting (and return those IDs in the result).
1. It must register IDs concurrenty but there should never be more than 10 requests in-flight.
 
## API Requirements
1. An HTTP API must be implemented for machine consumption of the service/functionality
1. The response is JSON representation: `{“deveuis”: [“FFA45722AA738240”,....]}`
1. The API must be idempotent

## LoRaWAN API

<pre>
host: ***
paths:
	/sensor-onboarding-sample:
		post:
			consumes:
				- application/json
			parameters:
				- in: body
				- required: true
				- type: string
				- name: deveui
			responses:
				200:
					description: The device has been successfully registered
				422:
					description: The devEUI has already been used
</pre>

# High-level Design Ideas
1. create a module/class for the generic logic (class `deveui_batch.BatchRegistration`) and decouple communication with the HTTP API, so that it can be unit tested by using a mock function/interface in the unit tests.
1. The module itself serves as the CLI tool (when run directly)
1. The module can be imported to the application implementing the REST API

## API Design

See [openapi/specification.yml](openapi/specification.yml) for details.

Client pseudo code to use the API:
<pre>
base_URI = /api/v1/
1. POST /batches  (param: batch_size, default=100)
	-> 201 Created
		batch_URI = headers.location (/batches/1)
2. GET $batch_URI
	-> 200 OK
		if body.json.status == "Processing":
			wait and repeat...
		elif body.json.status == "Completed"
			devEUI_list = body.json.deveuis
		else: error
3. persist $devEUI_list
4. DELETE $batch_URI
</pre>

![](sequence-diagram.png)

Ways to scale this:
- assume that there can be multiple clients that need their individual batches in parallel:
	The POST request should contain a unique client ID. The batch ID encodes that client ID (instead of const "1"). Processing of different batches can be passed on to different servers by an API gateway, e.g by using a consistent hashing algorithm on the batch ID. Perhaps DELETE method on the collection should not be allowed.
- if batch size increases..., a new version of the API could introduce batch partitions ( `/batches/1/partitions/1`). GET `/batches/1` would return a HATEOAS-style list of links to the partition URIs. Each partition could have `status=="Processing"` that indicates that the client needs to poll.

## Known Limitations / Ways to Improve
1. A `concurrent.futures.ThreadPoolExecutor` was used (default 10 workers). Non-threaded couroutines with an event loop is more lightweight and generally safer (but also needs a lot more thinking to make it right).
1. No authN/authZ on the API at the moment
1. NotYetImplemented: although the API does queue and process multiple requests, handling of multiple `batch` resources is not implemented yet, there is only a single batch (const `batch/1`) that gets overwritten with the result of consecutive requests 
1. NotYetImplemented: simialrly, only the stub exists for getting all or deleting any of the `batch` resources.
1. The current implementation probably fails the "idempotency" requirement (depends how you look at it). One solution could be, for instance, with a few lines of code change that the API takes a unique client-specific ID in the POST `/api/v1/batch` request, and if a resource `/api/v1/batch/{client_id}` already exisits then the API just returns the Location of, instead of replacing the const `/api/v1/batch/1` resource with a new batch of IDs. Otherwise, with the current implementation, the client could just check if the resource `/api/v1/batch/1` already exisits.
1. The API has no data persistence, it's completely in-memory. To avoid "wasting" those precious devEUIs, a scenario of API restart (or in the future re-balancing) should be taken into account, and data persisted in a distributed datastore.
