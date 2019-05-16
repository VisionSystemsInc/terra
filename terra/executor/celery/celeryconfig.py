#!/usr/bin/env python

import importlib
from os import environ as env
import os

with open(os.path.join(env['TERRA_CWD'], env['TERRA_REDIS_SECRET_FILE']), 'r') as fid:
  password = fid.readline().rstrip('\r\n')

broker_url = f'redis://:{password}@{env["TERRA_REDIS_HOSTNAME"]}:{env["TERRA_REDIS_PORT"]}/0'
result_backend = broker_url

task_serializer='pickle'
accept_content=['json', 'pickle']
result_expires=3600

# App needs to define include
celery_include = env.get('TERRA_CELERY_INCLUDE', None)
if celery_include:
  include = ast.literal_eval(celery_include)
