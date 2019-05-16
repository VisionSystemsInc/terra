FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini-musl as tini
FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:pipenv as pipenv

###############################################################################

FROM python:3.7.3-alpine3.8 as dep_stage
SHELL ["/usr/bin/env", "sh", "-euxvc"]

# Install any runtime dependencies
RUN apk add --no-cache bash libressl

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/terra/Pipfile \
    PIPENV_CACHE_DIR=/venv/cache \
    # Needed for pipenv shell
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

COPY --from=pipenv /tmp/pipenv /tmp/pipenv
RUN /tmp/pipenv/get-pipenv; rm -rf /tmp/pipenv || :

###############################################################################

FROM dep_stage as pipenv_cache

RUN apk add --no-cache gcc g++ libffi-dev libressl-dev make

ADD external/vsi_common/setup.py /vsi/
ADD setup.py Pipfile Pipfile.lock /terra/

    # Install all packages into the image
RUN mkdir -p /terra/external; \
    ln -s /vsi /terra/external/vsi_common; \
    (cd /vsi; /usr/local/pipenv/bin/fake_package vsi python/vsi); \
    (cd /terra; /usr/local/pipenv/bin/fake_package terra terra); \
    pipenv install --keep-outdated; \
    # Copy the lock file, so that it can be copied out of the image in "just _post_build"
    cp /terra/Pipfile.lock /venv; \
    # Cleanup and make way for the real /terra that will be mounted at runtime
    rm -rf /terra/* /tmp/pip*

###############################################################################

FROM dep_stage

# Recipes
COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu
COPY --from=pipenv_cache /venv /venv
COPY --from=vsi /vsi /vsi

# Terra
ADD terra.env /terra/
ADD docker/terra.Justfile /terra/docker/

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_entrypoint.sh"]

CMD ["bash"]
