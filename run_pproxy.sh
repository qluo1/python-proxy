#!/bin/bash

source .venv/bin/activate

rm log/pproxy.*

exec python -m pproxy -l http://localhost:8080
