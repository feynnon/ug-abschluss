# ERiC (Linux x86_64) – läuft auf Apple Silicon über Emulation (--platform linux/amd64).
# ERiC selbst wird NICHT ins Image kopiert (Lizenz, Größe), sondern zur Laufzeit gemountet:
#   docker run --rm --platform linux/amd64 -v ~/Downloads/eric/linux/ERiC-<ver>/Linux-x86_64:/eric:ro ug-eric
FROM --platform=linux/amd64 debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ENV LD_LIBRARY_PATH=/eric/lib
WORKDIR /work
CMD ["/eric/bin/ericSystemCheck"]
