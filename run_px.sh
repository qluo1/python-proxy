#!/bin/bash


source .venv/bin/activate

exec python -m px.server --config px/config/settings.toml
