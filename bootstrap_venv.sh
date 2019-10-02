#!/bin/bash

CUR_DIR=${PWD##}
VENV=${1:-.venv}
unset HTTP_PROXY
unset PYTHONPATH

################
## bootstrap virtualenv and create .local
export GS_PYPI_URL="http://devpi.qaauto.url.gs.com:8040/root/qaauto"
export GS_PYPI_HOST="devpi.qaauto.url.gs.com"


GNS_PY3=/sw/external/python-3.7.1
# GNS_PY3=/sw/external/python-3.6.8


# latest python3
PYTHON=$GNS_PY3/bin/python3


# GCC 5.2.1
source /gns/mw/lang/c/devtoolset-4.0-1.gns/enable

# create venv
$PYTHON -m venv ${VENV}
# generate local pip.conf
cat > ${VENV}/pip.conf <<END

[global]
timeout = 60
index-url = ${GS_PYPI_URL}
trusted-host = ${GS_PYPI_HOST}
END

# install pip-tools
source ${VENV}/bin/activate
echo "install pip-tools"
pip install pip-tools -i ${GS_PYPI_URL} --trusted-host ${GS_PYPI_HOST}

echo "sync packages"
pip-sync
