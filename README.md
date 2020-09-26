# DevEUI batch creation coding challenge

## Tool (CLI) Requirements
1. It must register each DevEUI of the batch (of deafult size 100) with the LoRaWAN provider, and must expect and handle DevEUI conflicts
1. DevEUI format is 16 hex characters
1. The 5-character code (last 5 chars of DevEUI) must be unique within a batch
1. DevEUIs must not be wasted, the tool must return every ID that it registers. The tool must handle interrupts (SIGINT) gracefully, and finish the registrations in-flight before exiting (and return those IDs in the result).
1. It must register IDs concurrenty but there should never be more than 10 requests in-flight.
 
## API Requirements
1. An HTTP API must be implemented for machine consumption of the service/functionality
1. The response is JSON representation: `{“deveuis”: [“FFA45722AA738240”,....]}`

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

## API Design

Client pseudo code to use the API:
<pre>
base_URI = /device-id-api/v1/
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

Ways to scale this:
- assume that there can be multiple clients that need their individual batches in parallel:
	The POST request should contain a unique client ID. The batch ID encodes that client ID (instead of const "1"). Processing of different batches can be passed on to different servers by an API gateway, e.g by using a consistent hashing algorithm on the batch ID. Perhaps DELETE method on the collection should not be allowed.
- if batch size increases..., a new version of the API could introduce batch partitions ( `/batches/1/partitions/1`). GET `/batches/1` would return a HATEOAS-style list of links to the partition URIs. Each partition could have `status=="Processing"` that indicates that the client needs to poll.


