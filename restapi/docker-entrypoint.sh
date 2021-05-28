#!/bin/bash
set -e

if [ "$stage_app" = 'production' ]; then
  uvicorn app:app --host 0.0.0.0 --proxy-headers
else
  uvicorn app:app --host 0.0.0.0 --proxy-headers --reload
fi
