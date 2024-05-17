FROM i2incommon/shib-idp:latest4

# The build args below can be used at build-time to tell the build process where to find your config files.  This is for a completely burned-in config.
ARG TOMCFG=config/tomcat
ARG TOMCERT=credentials/tomcat
ARG TOMWWWROOT=wwwroot
ARG SHBCFG=config/shib-idp/conf
ARG SHBCREDS=credentials/shib-idp
ARG SHBVIEWS=config/shib-idp/views
ARG SHBEDWAPP=config/shib-idp/edit-webapp
ARG SHBMSGS=config/shib-idp/messages
ARG SHBMD=config/shib-idp/metadata

# copy in the needed config files
ADD ${TOMCFG} /usr/local/tomcat/conf
ADD ${TOMCERT} /opt/certs
ADD ${TOMWWWROOT} /usr/local/tomcat/webapps/ROOT
ADD ${SHBCFG} /opt/shibboleth-idp/conf
ADD ${SHBCREDS} /opt/shibboleth-idp/credentials
ADD ${SHBVIEWS} /opt/shibboleth-idp/views
#ADD ${SHBEDWAPP} /opt/shibboleth-idp/edit-webapp
#ADD ${SHBMSGS} /opt/shibboleth-idp/messages
ADD ${SHBMD} /opt/shibboleth-idp/metadata
