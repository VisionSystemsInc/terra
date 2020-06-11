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

## Setting up pipenv

There are a number of reasons `pipenv` running python 3.6 or newer may not be available, especially on older operating systems. To automatically setup `pipenv` in a directory for you, run `just terra setup --dir {directory to install pipenv in}`. This does not require elevated permissions.

`just terra setup` will attempt to setup pipenv using a series of different strategies:

1. It will look for the Python 3 executable (`python3` or `python`). If this is found, it will be used to setup `pipenv`
  - A specific python executable can be specified using the `--python` flag
2. If `python` cannot be found, it will look for the `conda3`/`conda`/`conda2` executable and use that to first setup Python 3.7, and then setup `pipenv`
  - A specific executable of conda can be specified using the `--conda` flag
3. If all else fails, MiniConda will be downloaded from the internet, installed, and used to first setup Python 3.7, and then setup `pipenv`
4. If an invalid version of python or conda is detected, the download approach can be forced using the `--download` flag.
5. If for some reason, `curl`/`wget`/`perl`/`python`/`ruby` have an https error downloading miniconda when using the `--download` flag, then the `--conda-install` flag can be used to point to a pre-downloaded version of the anaconda or miniconda installer.
6. Once `pipenv` is setup, it should be added to your `PATH` using the `local.env` file. This will be done for you if you answer yes to the final question at the end.

## Running an app in celery

1. `just terra up` - To start redis queue (only once)
2. `just run celery` - To start a celery worker (run on each worker node)
3. `just run dsm ...` - To start processing job

When done
4. `just shutdown celery` - To shutdown _all_ celery workers on _all_ nodes
5. `just terra down` - To shutdown redis.