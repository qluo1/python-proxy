#!/bin/bash
CUR_DIR=$(dirname "${BASH_SOURCE[0]}")

tk_file=/local/data/home/eqtdata/sandbox/luosam/keytab/luosam.keytab

# ensure tk available
/usr/kerberos/bin/kinit luosam -k -t $tk_file

unset HTTPS_PROXY
unset HTTP_PROXY

source $CUR_DIR/.venv/bin/activate

exec python3 -m px.server --config px/config/settings.toml
