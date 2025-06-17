#!/bin/bash

# Load Python module
module load python

# Activate virtual environment
source venv/bin/activate

# Start the gateway with rate limiting and logging
uvicorn src.middleware:app --host 0.0.0.0 --port 8000 \
    --ssl-keyfile certificates/key.pem \
    --ssl-certfile certificates/cert.pem
