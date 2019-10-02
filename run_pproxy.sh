#!/bin/bash

source .venv/bin/activate

exec python -m pproxy -l http://localhost:8080
