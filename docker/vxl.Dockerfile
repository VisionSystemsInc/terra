FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:pipenv as pipenv
# # Uncomment for GDAL
# FROM vsiri/recipe:jq as jq

FROM debian:stretch as dep_stage
SHELL ["/usr/bin/env", "bash", "-euxvc"]

# Install any runtime dependencies
RUN apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      # # Uncomment for GDAL
      # gdal-bin \
      python3; \
    rm -r /var/lib/apt/lists/*

ENV \
    # Move all virtualenvs to /venv
    WORKON_HOME=/venv \
    PIPENV_PIPFILE=/src/Pipfile \
    # The pipenv cache is how we avoid recompiling packages at runtime
    # when the build dependencies are no longer available
    PIPENV_CACHE_DIR=/venv/cache \
    # Needed for pipenv shell
    PYENV_SHELL=/bin/bash \
    # pipenv recommends that these env variables be set to en_US.UTF-8.
    # On debian, C.UTF-8 exists by default instead, and seems to work.
    # More detail: https://stackoverflow.com/a/38553499/1771778
    # Note: en_US.UTF-8 exists by default in Centos/Fedora base images
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

COPY --from=pipenv /tmp/pipenv /tmp/pipenv
RUN /tmp/pipenv/get-pipenv; rm -rf /tmp/pipenv || :

FROM dep_stage as pipenv_cache

# # Uncomment for GDAL
# # Install any build dependencies
# RUN apt-get update; \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#       libgdal-dev python3-dev g++ ; \
#     rm -r /var/lib/apt/lists/*
#
# COPY --from=jq /usr/local/bin/jq /usr/local/bin/jq

ADD Pipfile Pipfile.lock /src/
# Simple packages can be added as dependencies to your project by:
# - Running the container and installing them with pipenv; e.g.,
#     just run vxl
#     pipenv install --keep-outdated scipy
#     # install scipy without updating other packages
# Packages that require compiling should be added by
# - Editing the Pipfile and adding lines to the [packages] section
#     scipy = "*"
# - Rebuiling the image
#     just build

# GDAL, for example, is a more complicated example
# - GDAL has extra build dependencies. The apt-get pattern above will install
#   these dependencies.
# - GDAL's build script needs some customization. The exports
#   below accomplish this
# - GDAL needs numpy installed before it is built, otherwise, numpy
#   integration will not be compiled
#
# To test this out:
# 1) Edit your Pipfile and add the following lines (or similar)
#        gdal = "==2.1.0"
#        numpy = "*"
#    This will add the latest version of numpy and the version of
#    gdal compatible with debian:stretch to your pipenv environment.
#    Note: the version of the pypi package should match (as closely as
#    possible) to the version of the GDAL-binary dependency (gdal-bin)
# 2) Uncomment all the "Uncomment for GDAL" sections

# # Uncomment for GDAL
# RUN \
#     # GDAL specific hacks
#     export CPLUS_INCLUDE_PATH=/usr/include/gdal; \
#     export C_INCLUDE_PATH=/usr/include/gdal; \
#
#     # Get the version of numpy specified in the lock file, else blank
#     numpy_version="$(jq --raw-output ".default.numpy.version // empty" "${PIPENV_PIPFILE}".lock)"; \
#     # Install numpy first; then the other packages are installed.
#     pipenv install --keep-outdated numpy${numpy_version}; \
#
#     cp "${PIPENV_PIPFILE}".lock /venv; \
#     rm -rf /src/* /tmp/pip*

RUN \
    # Install all packages into the image
    pipenv install --keep-outdated; \
    # Copy the lock file, so that it can be copied out of the image in "just _post_build"
    cp /src/Pipfile.lock /venv; \
    # Cleanup and make way for the real /src that will be mounted at runtime
    rm -rf /src/* /tmp/pip*

FROM dep_stage

# Install any additional packages
RUN apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      # Example of a package
      qbs-examples; \
    rm -rf /var/lib/apt/lists/*

# Another typical example of installing a package
# RUN build_deps="wget ca-certificates"; \
#     apt-get update; \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${build_deps}; \
#     wget -q https://www.vsi-ri.com/bin/deviceQuery; \
#     DEBIAN_FRONTEND=noninteractive apt-get purge -y --autoremove ${build_deps}; \
#     rm -rf /var/lib/apt/lists/*

COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini

COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu

COPY --from=pipenv_cache /venv /venv

COPY --from=vsi /vsi /vsi
ADD docker/vxl_entrypoint.bsh /
ADD vxl.env /src/

ENTRYPOINT ["/usr/local/bin/tini", "/usr/bin/env", "--", "bash", "/vxl_entrypoint.bsh"]
# Does not require execute permissions, unlike:
# ENTRYPOINT ["/usr/local/bin/tini", "/vxl_entrypoint.bsh"]

CMD ["vxl"]
