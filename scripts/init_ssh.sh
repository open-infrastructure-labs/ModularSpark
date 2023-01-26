#!/bin/bash

set -e # exit on error
pushd "$(dirname "$0")" # connect to root
source ../version

ROOT_DIR=$(pwd)
echo "ROOT_DIR ${ROOT_DIR}"

USER_NAME=${SUDO_USER:=$USER}

echo $BASE_STORAGE_CONTAINER_NAME-0
# Create ssh authorized_keys
docker exec -it $BASE_STORAGE_CONTAINER_NAME-0 cat ~/.ssh/id_rsa.pub >> ./authorized_keys
docker exec -it $BASE_SPARK_CONTAINER_NAME-dc1 cat ~/.ssh/id_rsa.pub >> ./authorized_keys

chmod 600 ./authorized_keys
mkdir -p ${ROOT_DIR}/../storage/volume/ssh
mkdir -p ${ROOT_DIR}/../spark/volume/ssh
mkdir -p ${ROOT_DIR}/../spark/extensions/server/volume/ssh

cp ./authorized_keys ${ROOT_DIR}/../storage/volume/ssh
cp ./authorized_keys ${ROOT_DIR}/../spark/volume/ssh
cp ./authorized_keys ${ROOT_DIR}/../spark/extensions/server/volume/ssh

rm -f ./authorized_keys

echo "StrictHostKeyChecking no" > ./ssh_config
cp ./ssh_config ${ROOT_DIR}/../storage/volume/ssh/config
cp ./ssh_config ${ROOT_DIR}/../spark/volume/ssh/config
cp ./ssh_config ${ROOT_DIR}/../spark/extensions/server/volume/ssh/config

rm -f ./ssh_config
