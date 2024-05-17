#!/bin/bash

echoerr() { echo "$@" 1>&2; }

set -e

function set_map_node_info() {
  echo "${MAP_CERT}" > temp.txt
  if [ "$(uname)" == "Darwin" ]
  then
    # For Mac OS platform
    sed -i '' -e "/__MAP_CERT__/r temp.txt"  -e "/__MAP_CERT__/d" $1
    sed -i '' -e "s|__MAP_HOST_NAME__|$2|g" -e "s|__MAP_HOST_PORT__|$3|g" $1
  else
    sed -i -e "/__MAP_CERT__/r temp.txt"  -e "/__MAP_CERT__/d" $1
    sed -i -e "s|__MAP_HOST_NAME__|$2|g" -e "s|__MAP_HOST_PORT__|$3|g" $1
  fi
  rm -f temp.txt
}

function help_message() {
  echo "This script generates configuration files for Shibboleth"
  echo "to support Single Sign-On in the GREN Map DB Node."
  echo "Options:"
  echo -e "\t[-m number] --number of GREN Map DB Nodes to configure. Defaults to 1."
  exit 1
}

while getopts ":m:" flag
  do
    case "${flag}" in
        m)  MAP_NUMBER=$OPTARG
            if ! [[ $MAP_NUMBER -gt 0 ]] ; then
              echoerr "Error: -m # must be a whole number larger than 0."
              help_message
            fi ;;
        :)  echoerr "Error: -${OPTARG} requires an argument."
            help_message ;;
        *)  help_message ;;
    esac
  done

if (! docker stats --no-stream >/dev/null 2>&1 )
then
  echoerr "Error: Docker daemon is NOT running. Please start it before run this script."
  exit 1
fi

echo
echo "=================================================================================="
echo "Exporting environment variables from /.env ..."
if [ -f .env ]
then
  source .env
else
  echoerr "Error: Please create an '.env' file according to 'env_example' file in the project root folder."
  exit 1
fi
echo "... Done."

# Check whether IdP host is reachable or added to /etc/host
if (! grep -Fiq ${IDP_HOST_NAME} /etc/hosts ) && (! nc -zv ${IDP_HOST_NAME} 443 >/dev/null 2>&1 )
then
  echoerr "Error: Please add ${IDP_HOST_NAME} to /etc/hosts for your local operating system."
  exit 1
fi

if [[ -z "$MAP_NUMBER" ]]
then
  MAP_NUMBER=1
fi

echo
echo "=================================================================================="
echo "Generating the list of metadata providers..."
METADATA_PROVIDERS=""
i=$MAP_NUMBER
while [[ $i -gt 0 ]]
do
  eval host_name=\$MAP${i}_HOST_NAME
  eval host_port=\$MAP${i}_HOST_PORT
  if [[ -z ${host_name} ]] || [[ -z ${host_port} ]]
  then
    echoerr "Error: Please set up MAP${i}_HOST_NAME and MAP${i}_HOST_PORT in the '/.env' file for all ${MAP_NUMBER} GREN Map DB Nodes."
    exit 1
  elif (! grep -Fiq ${host_name} /etc/hosts )
  then
    echoerr "Error: Please add ${host_name} to /etc/hosts for your local operating system."
    exit 1
  else
    METADATA_PROVIDERS+=$(printf '%s' "<MetadataProvider id=\"LocalMetadata${i}\" xsi:type=\"FilesystemMetadataProvider\" metadataFile=\"/opt/shibboleth-idp/metadata/map${i}-metadata.xml\"/>")$'\n'
  fi
  i=$(($i-1))
done
echo "... Done."

echo
echo "=================================================================================="
echo "Generating certificate files for Shibboleth..."
./websp/shibboleth_keygen.sh -o ./websp/configs_and_secrets -f -h ${MAP1_HOST_NAME} -y 10 -n sp
echo "... Done."

# Get MAP certificate
MAP_CERT="$(grep -v '^-----' ./websp/configs_and_secrets/sp-cert.pem)"

echo
echo "=================================================================================="
echo "Generating certificate files for Apache..."
./websp/shibboleth_keygen.sh -o ./websp/configs_and_secrets -f -h ${MAP1_HOST_NAME} -y 10 -n host
echo "... Done."

# Run the config builder to generate IdP configuration files
echo
echo "=================================================================================="
echo "Runing IdP config builder..."
printf "%s\n" ${IDP_HOST_NAME} "Y" "example.org" "Y" "ldap://openldap:1389" "Y" "ou=People,dc=example,dc=org" "Y" "cn=admin,dc=example,dc=org" "Y" "${LDAPPWD}" "Y" | docker run --rm -i -v ${PWD}/idp/container_files:/output -e "BUILD_ENV=LINUX" tier/shibbidp_configbuilder_container
echo "... Done."

# Delete the unneeded file
rm -f ./idp/container_files/Dockerfile

echo
echo "=================================================================================="
echo "Copying customized Shibboleth config files to the IdP config..."
cp -rf ./idp/templates/conf/* ./idp/container_files/config/shib-idp/conf/
echo "... Done."

echo
echo "=================================================================================="
echo "Creating metadata files for additional GREN Map DB Nodes..."
i=$MAP_NUMBER
while [[ $i -gt 0 ]]
do
  eval host_name=\$MAP${i}_HOST_NAME
  eval host_port=\$MAP${i}_HOST_PORT
  FILE="./idp/container_files/config/shib-idp/metadata/map${i}-metadata.xml"
  cp -rf ./idp/templates/metadata/map-metadata.xml $FILE
  set_map_node_info ${FILE} ${host_name} ${host_port}
  i=$(($i-1))
done
echo "... Done."

echo
echo "=================================================================================="
echo "Adding metadata snippets to metadata-providers.xml ..."
FILE="./idp/container_files/config/shib-idp/conf/metadata-providers.xml"
echo "${METADATA_PROVIDERS}" > temp.txt
if [ "$(uname)" == "Darwin" ]
then
  # For Mac OS platform
  sed -i '' -e "/<!--__METADATA_PROVIDERS__-->/r temp.txt"  -e "/<!--__METADATA_PROVIDERS__-->/d" $FILE
else
  sed -i -e "/<!--__METADATA_PROVIDERS__-->/r temp.txt"  -e "/<!--__METADATA_PROVIDERS__-->/d" $FILE
fi
rm -f temp.txt
echo "... Done."

echo
echo "=================================================================================="
echo "Coping the IdP metadata file to the websp container..."
cp ./idp/container_files/config/shib-idp/metadata/idp-metadata.xml ./websp/configs_and_secrets/idp_metadata/
echo "... Done."

echo
echo "The configuration completed successfully."
echo
echo "Remember to add the GREN Map DB Node host names to DJANGO_ALLOWED_HOSTS in the relevant env/.env* file(s)."
