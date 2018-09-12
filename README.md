# mock-exchange

A mock exchange for testing purposes. 
☠☠ THIS IS WORK IN PROGRESS  ☠☠

* [Please report any bugs / issues here](https://gitlab.com/swissborg/oms/mock-exchange/issues/new)


# Prerequisites

1. Python 3.7 

2. Redis 5.0 (yes the beta version 🙈)

# Run the mock exchange

1. Install prerequisites in the machine

2. Run redis server by using command: `redis-server`

3. Run REST API server by using command: `make api`

4. Run Websocket Interface by using command: `make websocket`

# How to use
1. The REST API server spins up at `localhost:8000`

2. Health check `/ping/`

3. localhost:8000/orders/

