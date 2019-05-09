#!/usr/bin/env python

from os import environ as env
import os

with open(os.path.join(env['TERRA_CWD'], env['TERRA_REDIS_SECRET_FILE']), 'r') as fid:
  password = fid.readline().rstrip('\r\n')

broker_url = f'redis://:{password}@{env["TERRA_REDIS_HOSTNAME"]}:{env["TERRA_REDIS_PORT"]}/0'
result_backend = broker_url

task_serializer='pickle'
accept_content=['json', 'pickle']
result_expires=3600

include=['terra.apps.task.viewangle']
