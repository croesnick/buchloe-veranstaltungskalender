#!/usr/bin/env bash

mkdir -p data

python scraper.py | tee "data/$(date -Iseconds).json"
