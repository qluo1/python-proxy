#!/bin/bash

port=${1:-8080}

curl -v https://gitlab.gs.com/eq-tech/eq-test-engineering/qfix/blob/dev/QFIX/QA.config  -x http://localhost:${port} --trace trace_ssl_url.txt
