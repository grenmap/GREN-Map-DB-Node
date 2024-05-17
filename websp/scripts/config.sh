#!/bin/bash

files="/etc/shibboleth/shibboleth2.xml /etc/httpd/conf.d/ssl.conf /var/www/html/shibboleth-ds/idpselect_config.js"

if [ -z "$IDP_SSO" ]
then
  echo "Use the default IdP SSO"
  IDP_SSO='<SSO discoveryProtocol="SAMLDS" discoveryURL="https://__MAP_HOST_NAME__:__MAP_HOST_PORT__/shibboleth-ds/index.html">SAML2 SAML1</SSO>'
fi

if [ -z "$METADATA_PROVIDERS" ]
then
  echo "Use the default METADATA_PROVIDERS"
  METADATA_PROVIDERS='<MetadataProvider type="XML" validate="true" path="/etc/shibboleth/idp-metadata.xml"/>'
fi

for file in $files
  do
    if [ "$file" = "/etc/shibboleth/shibboleth2.xml" ]
    then
      echo "Update shibboleth2.xml"
      echo "$IDP_SSO" > temp.txt
      sed -i -e "/<!--__IDP_SSO__-->/r temp.txt"  -e "/<!--__IDP_SSO__-->/d" $file
      echo "$METADATA_PROVIDERS" > temp.txt
      sed -i -e "/<!--__METADATA_PROVIDERS__-->/r temp.txt"  -e "/<!--__METADATA_PROVIDERS__-->/d" $file
      rm -f temp.txt
    fi
    sed -i "s|__MAP_HOST_NAME__|$MAP_HOST_NAME|g" $file
    sed -i "s|__MAP_HOST_PORT__|$MAP_HOST_PORT|g" $file
    sed -i "s|__IDP_HOST_NAME__|$IDP_HOST_NAME|g" $file
  done

echo "Substitute template done"

# If encoded EDS logo image file exists, decode it
LOGO_FILE=/var/www/html/shibboleth-ds/eds_logo.png
if [[ -f "$LOGO_FILE.encoded" ]]
then
  base64 -d "$LOGO_FILE.encoded" > "$LOGO_FILE"
fi
