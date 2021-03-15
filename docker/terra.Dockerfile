# syntax=docker/dockerfile

FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini-musl as tini
FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:pipenv as pipenv

###############################################################################

FROM python:3.7-alpine as dep_stage
SHELL ["/usr/bin/env", "sh", "-euxvc"]

# Install any runtime dependencies
RUN apk add --no-cache bash libressl tzdata

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/terra/Pipfile \
    PIPENV_CACHE_DIR=/venv/cache \
    # Needed for pipenv shell
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

COPY --from=pipenv /usr/local /usr/local
RUN for patch in /usr/local/share/just/container_build_patch/*; do "${patch}"; done

###############################################################################

FROM dep_stage as pipenv_cache

RUN apk add --no-cache gcc g++ libffi-dev libressl-dev make linux-headers

COPY external/vsi_common/setup.py /terra/external/vsi_common/
COPY setup.py Pipfile Pipfile.lock /terra/

    # Install all packages into the image
RUN (cd /terra/external/vsi_common; /usr/local/pipenv/bin/fake_package vsi python/vsi); \
    (cd /terra; /usr/local/pipenv/bin/fake_package terra terra); \
    pipenv sync; \
    # Cleanup and make way for the real /terra that will be mounted at runtime
    rm -rf /terra/* /tmp/pip*

###############################################################################

FROM pipenv_cache as pipenv_run

COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]

CMD ["bash"]

###############################################################################

FROM dep_stage

# Recipes
COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu
COPY --from=pipenv_cache /venv /venv
COPY --from=vsi /vsi /vsi

# Terra
COPY terra.env /terra/
COPY docker/terra.Justfile /terra/docker/

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]

CMD ["bash"]
