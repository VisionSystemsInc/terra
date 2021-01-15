#!/usr/bin/env python

from os import environ as env
import os

from terra.logger import getLogger
logger = getLogger(__name__)

# Put all celery values set here, so an app can inherit the config by saying:
# from terra.executor.celery.celeryconfig import *
__all__ = ['password', 'broker_url', 'result_backend', 'task_serializer',
           'result_serializer', 'accept_content', 'result_accept_content',
           'result_expires', 'include']

try:
  with open(os.path.join(env['TERRA_CWD'], env['TERRA_REDIS_SECRET_FILE']),
            'r') as fid:
    password = fid.readline().rstrip('\r\n')
except FileNotFoundError:
  logger.fatal(os.path.join(env['TERRA_CWD'], env['TERRA_REDIS_SECRET_FILE'])
               + ": Redis password file not found. "
               + "'just' should auto generate this")
  raise

broker_url = f'redis://:{password}@{env["TERRA_REDIS_HOSTNAME"]}:' \
             f'{env["TERRA_REDIS_PORT"]}/0'
result_backend = broker_url

task_serializer = 'pickle'
result_serializer = 'pickle'
accept_content = ['json', 'pickle']
result_accept_content = ['json', 'pickle']
result_expires = 3600

# App needs to define include
include = []
_include_env_var = env.get('TERRA_CELERY_INCLUDE', None)
if _include_env_var:
  import ast
  include = ast.literal_eval(_include_env_var)
  include += type(include)(['terra.tests.demo.tasks'])

# This is how it was done in Voxel Globe, but some detail is missing
# from kombu import Queue, Exchange
# task_queues = (
#     Queue('gpu', exchange=Exchange('default', type='direct'),
#           routing_key='gpu'),
# )

# This is "Automatic routing", but a less preferred method
# task_routes = {'dsm.tasks.match_features.*': {'queue': 'gpu'}}

# task_default_queue = 'cpu' # This works!
# task_default_exchange = 'default' # Doesn't seem to do anything
# Doesn't seem to do anything, even with default_exchange
# task_default_routing_key = 'cpu'