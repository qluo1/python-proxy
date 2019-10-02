#!/bin/bash


source .venv/bin/activate

rm log/px.log*

exec python -m px.server --config px/config/settings.toml
