FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:ninja as ninja
FROM vsiri/recipe:cmake as cmake
FROM vsiri/recipe:pipenv as pipenv

###############################################################################

FROM debian:stretch as dep_stage
SHELL ["/usr/bin/env", "bash", "-euxvc"]

# Install any runtime dependencies
RUN apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3 libgeotiff2 libgomp1; \
    rm -r /var/lib/apt/lists/*

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/src/Pipfile \
    PIPENV_CACHE_DIR=/venv/cache \
    # Needed for pipenv shell
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

COPY --from=pipenv /tmp/pipenv /tmp/pipenv
RUN /tmp/pipenv/get-pipenv; rm -rf /tmp/pipenv || :

###############################################################################

FROM dep_stage as pipenv_cache

ADD Pipfile Pipfile.lock /src/

    # Install all packages into the image
RUN pipenv install --keep-outdated; \
    # Copy the lock file, so that it can be copied out of the image in "just _post_build"
    cp /src/Pipfile.lock /venv; \
    # Cleanup and make way for the real /src that will be mounted at runtime
    rm -rf /src/* /tmp/pip*

###############################################################################

FROM dep_stage as compile

# Install any additional packages
RUN apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      # Example of a package
      g++ python3-dev libgeotiff-dev; \
    rm -rf /var/lib/apt/lists/*

COPY --from=ninja /usr/local/bin/ninja /usr/local/bin/ninja
COPY --from=cmake /cmake /usr/local/
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
RUN chmod u+s /usr/local/bin/gosu

# COPY --from=pipenv_cache /venv /venv

COPY --from=vsi /vsi /vsi

ADD docker/terra_entrypoint.bsh /
ADD terra.env /src/

ENTRYPOINT ["/usr/bin/env", "--", "bash", "/terra_entrypoint.bsh"]

CMD ["compile"]

###############################################################################

FROM dep_stage

COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu

COPY --from=pipenv_cache /venv /venv

COPY --from=vsi /vsi /vsi
ADD docker/terra_entrypoint.bsh /
ADD terra.env /src/

ENTRYPOINT ["/usr/local/bin/tini", "/usr/bin/env", "--", "bash", "/terra_entrypoint.bsh"]

CMD ["bash"]
