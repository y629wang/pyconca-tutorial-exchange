# mock-exchange

A mock exchange for testing purposes. 
☠☠ THIS IS WORK IN PROGRESS  ☠☠ Do not deploy it in production for real money!



# Prerequisites

1. Docker and Docker compose

2. This application uses two ports, 8000 and 8765. Make sure those are available on your machine. 

# Run the mock exchange

1. Install prerequisites in the machine

2. Make sure src/config.py has REDIS_PATH = 'redis'. 

3. Build Step `docker build -t mock_exchange .`

4. Run Step `docker-compose up`

# How to use
1. The REST API server spins up at `localhost:8000`

2. Websocket server spins up at `localhost:8765`

2. Health check `/ping/`
