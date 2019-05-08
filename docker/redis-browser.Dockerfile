# FROM vsiri/recipe:ep as ep
FROM ruby:2.6.3-alpine3.9

SHELL ["/usr/bin/env", "sh", "-euxvc"]

RUN apk add --no-cache gcc g++ make nodejs; \
    gem install redis-browser; \
    apk del --no-cache gcc g++ make

# COPY --from=ep /usr/local/bin/ep /usr/local/bin/ep

ADD docker/redis-browser.yaml /

# CMD ep /redis-browser.yaml; \
CMD echo -n $'\n    auth: ' | cat - /run/secrets/redis_password >> /redis-browser.yaml; \
    redis-browser --config /redis-browser.yaml --bind 0.0.0.0 --port 4567