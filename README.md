Terra project from VSI

[![CircleCI](https://circleci.com/gh/VisionSystemsInc/terra.svg?style=shield)](https://circleci.com/gh/VisionSystemsInc/terra)

## Requirements

- Python 3.6 or newer
- pipenv
- docker
- bash
- docker-compose

## Getting started

```
source 'setup.env'
just terra sync
just terra run
```

## Running an app in celery

1. `just terra up` - To start redis queue (only once)
2. `just run celery` - To start a celery worker (run on each worker node)
3. `just run dsm ...` - To start processing job

When done
4. `just shutdown celery` - To shutdown _all_ celery workers on _all_ nodes
5. `just terra down` - To shutdown redis.