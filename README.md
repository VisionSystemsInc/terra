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
3. `just run {app} ...` - To start processing job

When done
4. `just shutdown celery` - To shutdown _all_ celery workers on _all_ nodes
5. `just terra down` - To shutdown redis.

## Deploying a Terra App

These commands should be run from the app's just project directory, not Terra's or VSI Common's. Running these commands from the wrong project result in the wrong directory path transformations, and the resulting `just` executable will probably not work.

- It is probably best to not use the system's python, if you want a portable deployment:
    - `just terra setup --download --dir {some dir}` # to setup a conda python
    - `just --wrap Terra_Pipenv --rm` # to remove the old pipenv
- `just sync` # Sync your app and terra
- `just makeself` # To create a makeself. This should call `justify terra makeself` internally
- `just terra pyinstaller`
- `just deploy` # (not optional if using singularity:) to build docker images
- `just deploy singular` # (optional) If your app has this, and you want to use singularity

### How to use

After `makeself` and `pyinstaller` are run, you will have a `./just` project executable to run all just related tasks, and `{app name}` executables too. By default, the app executables should be in the same directory as the `./just` executable, but may be moved by setting the `TERRA_RUN_DIR` environment variable in `local.env` (see below).

#### local.env

Since there is no project directory, a `local.env` is first searched for in the directory of the `./just` executable, and loaded. After that, the current working directory is searched for a `local.env` file too, and loaded. This means it is possible for up to two `local.env` files to be loaded. In a multi-user environment, the `local.env` file in the `./just` directory should be used for containing values to make your app run for everyone, and the other `local.env` for any customizations a user needs for themselves or even multiple project (in multiple directories).

### Common deployment issues:

- `./just: line 662: ./external/terra/external/vsi_common/freeze/just_wrapper: Permission denied`
    - This happen in the very uncommon case when the `/tmp` folder has `noexec` on it. This is a form of fake security that can only lead to things breaking.
    - Solution: Set TMPDIR to a folder you do have exec permissions on, such as your home
    - Example: `TMPDIR=~/ ./just ...`
- `sed: invalid option -- 'E'`
    - On ancient versions of sed, only the `-r` option is accepted, and does not accept the BSD compatible `-E` version of the same flag
    - Solution: You should no longer need to do this, it is auto detected, but setting `VSI_SED_COMPAT` to `gnu` disables BSD compatibility mode.
    - Example: `VSI_SED_COMPAT=gnu ./just ...` or use `local.env`