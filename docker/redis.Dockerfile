FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini-musl as tini
FROM vsiri/recipe:vsi as vsi

FROM redis:5.0.4-alpine3.9

RUN apk add --no-cache bash tzdata gawk

COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
COPY --from=vsi /vsi /vsi

ADD terra.env /terra/
ADD docker/redis.Justfile /terra/docker/

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]

CMD ["redis-server"]