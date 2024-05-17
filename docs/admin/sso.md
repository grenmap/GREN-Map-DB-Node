# Production Single Sign On Support

Shibboleth Single Sign-on (SSO) has been used for user login and authorization.  Please contact your local Federation/IdP provider for assistance with configuring this service.

First, follow the relevant instructions in the Quick Start guide in README.md.  Then below, find some additional steps available to configure SSO for production deployments.

## IdP Metadata Provider

For production, ask the related IdP administrator to provide the proper configuration for MetadataProvider and IDP_SSO.  (IDP_HOST_NAME will be ignored unless "__IDP_HOST_NAME__" is included in the IDP_SSO string.)  Uncomment and update them in ".env" file, like

```
METADATA_PROVIDERS='<MetadataProvider
    type="XML" url="https://www.example.com/caf_test.xml"
    backingFilePath="federation-metadata.xml"
    reloadInterval="300"/>'
IDP_SSO='<SSO discoveryProtocol="SAMLDS" discoveryURL="https://www.example.com/discovery/WAYF">SAML2 SAML1</SSO>'
```
## Discovery Service

To use the Embedded Discovery Service(EDS) for development or production, add the following line to ".env" file.

```
IDP_SSO='<SSO discoveryProtocol="SAMLDS" discoveryURL="https://__MAP_HOST_NAME__:__MAP_HOST_PORT__/shibboleth-ds/index.html">SAML2 SAML1</SSO>'
```

### Embedded Discovery Service Logo

To use a custom EDS logo in the EDS page, create a logo image with similar dimension and size to the current "eds_logo.png", and mount it to the websp container like:

```
websp:
    ...
    volumes:
      ...
      - ./websp/your_custom_logo.png:/var/www/html/shibboleth-ds/eds_logo.png
```
