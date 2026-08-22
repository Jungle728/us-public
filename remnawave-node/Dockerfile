FROM ghcr.io/xtls/xray-core:26.6.27@sha256:c98160906f3fe1d9d16e950c2a7997dc0c542c71816aa92c21e510412f90e1a2 AS xray

FROM remnawave/node:3.3.2

COPY --from=xray /usr/local/bin/xray /usr/local/bin/xray
