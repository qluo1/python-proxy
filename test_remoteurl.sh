#!/bin/bash
port=${1:-8080}

curl -v https://github.com/qluo1  -x http://localhost:${port} --trace trace_ssl_remote.txt
