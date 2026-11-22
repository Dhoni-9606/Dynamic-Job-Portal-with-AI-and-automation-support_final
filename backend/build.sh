#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

<<<<<<< HEAD
python manage.py migrate
=======
python manage.py migrate
>>>>>>> 7ca664d99b4c2bbb8bc073b43cc975cdeb3786e6
