FROM i2incommon/shibboleth_sp:latest
LABEL ImageType="Shibboleth SP" \
      ImageName=$imagename \
      ImageOS=centos7

LABEL org.opencontainers.image.authors=$AUTHORS
LABEL org.opencontainers.image.created=$BUILD_TIMESTAMP
LABEL org.opencontainers.image.revision=$GIT_COMMIT
LABEL org.opencontainers.image.version=$GIT_TAG
LABEL org.opencontainers.image.description="GREN Map Database Node - websp image"

RUN yum -y update

COPY templates/502.html /var/www/html/502.html
COPY templates/gren-icon.png /var/www/html/gren-icon.png
COPY templates/shibboleth-ds/ /var/www/html/shibboleth-ds/

COPY templates/httpd/ /etc/httpd/conf.d/
COPY templates/shib/ /etc/shibboleth/

COPY configs_and_secrets/idp_metadata/ /etc/shibboleth/

RUN ln -sf /run/secrets/websp-host-key /etc/pki/tls/private/host-key.pem
RUN ln -sf /run/secrets/websp-host-cert /etc/pki/tls/certs/host-cert.pem
RUN ln -sf /run/secrets/websp-sp-key /etc/shibboleth/sp-key.pem
RUN ln -sf /run/secrets/websp-sp-cert /etc/shibboleth/sp-cert.pem

COPY scripts/config.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/config.sh

HEALTHCHECK --interval=1m --timeout=30s \
  CMD curl -k -f https://127.0.0.1:8443/Shibboleth.sso/Status || exit 1
 
EXPOSE 8443

ENTRYPOINT ["/bin/sh", "-c" , "/usr/local/bin/config.sh && /usr/local/bin/startup.sh"]
