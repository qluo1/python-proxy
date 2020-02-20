#!/bin/bash

tk_file=/local/data/home/eqtdata/sandbox/luosam/works/projects/gitlab/qaconsole/luosam.keytab

# ensure tk available
/usr/kerberos/bin/kinit luosam -k -t $tk_file

unset HTTPS_PROXY
unset HTTP_PROXY

exec  poetry run python3 -m px.server --config px/config/settings.toml
