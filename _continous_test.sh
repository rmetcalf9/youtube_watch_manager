#!/bin/bash

# not designed to be run directly. Run via test_continuous.sh

echo 'Start continuous test mode'

until ack -f --python  ./src ./test | entr -d python3 -m pytest -p no:cacheprovider; do sleep 1; done
