#!/bin/bash

curl -v https://gitlab.gs.com/eq-tech/eq-test-engineering/qfix/blob/dev/QFIX/QA.config  -x http://localhost:8080 --trace trace_ssl_url.txt
