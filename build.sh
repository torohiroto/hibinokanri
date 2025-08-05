#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python daily_management/manage.py collectstatic --no-input
python daily_management/manage.py migrate
