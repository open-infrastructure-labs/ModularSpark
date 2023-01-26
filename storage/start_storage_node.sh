#!/usr/bin/env bash

set -e # exit on error
pushd "$(dirname "$0")" # connect to root
ROOT_DIR=$(git rev-parse --show-toplevel)
source $ROOT_DIR/version

STORAGE_DIR=${ROOT_DIR}/storage

VALID_ARGS=$(getopt -o i: --longoptions node_id: -- "$@")
if [[ $? -ne 0 ]]; then
    exit 1;
fi

DC=dc1 # residue from QFlock project Data Center 1
NODE_ID=0 # set default node_id

eval set -- "$VALID_ARGS"
while [ : ]; do  
  case "$1" in
    -i | --node_id)
        echo "node_id = $2"
        NODE_ID=$2
        shift
        ;;
    --)
      break
      ;;
  esac
  shift
done


if [ ! -f ${STORAGE_DIR}/hadoop_home/etc/hadoop/core-site-${DC}.xml ]
  then
    echo "Error ${STORAGE_DIR}/hadoop_home/etc/hadoop/core-site-${DC}.xml does not exist"
    exit 1
fi

USER_NAME=${SUDO_USER:=$USER}
STORAGE_DOCKER_NAME="${BASE_STORAGE_DOCKER_NAME}-${USER_NAME}"

# Set the home directory in the Docker container.
HADOOP_HOME=/opt/hadoop/hadoop-3.3.0
HIVE_HOME=/opt/hive/apache-hive-3.1.2-bin # needs to be removed

NODE_PATH=${STORAGE_DIR}/volume/node-${NODE_ID}

# Create NameNode and DataNode mount points
mkdir -p ${NODE_PATH}/namenode
mkdir -p ${NODE_PATH}/datanode0
mkdir -p ${NODE_PATH}/logs

# Create Hive metastore directory
mkdir -p ${NODE_PATH}/metastore

# Create QFlock metastore directory
mkdir -p ${NODE_PATH}/metastore/qflock

# Create QFlock default catalog directory
mkdir -p ${NODE_PATH}/metastore/qflock/catalog/default

mkdir -p ${NODE_PATH}/status
rm -f ${NODE_PATH}/status/*

# Can be used to transfer data to HDFS
mkdir -p ${STORAGE_DIR}/data

CMD="bin/run_services.sh"
RUNNING_MODE="daemon"

# We need to be absolutely sure that ssh configuration exists
mkdir -p ${STORAGE_DIR}/volume/ssh
touch ${STORAGE_DIR}/volume/ssh/authorized_keys
touch ${STORAGE_DIR}/volume/ssh/config

DOCKER_RUN="docker run --rm=true ${DOCKER_IT} \
  -v ${STORAGE_DIR}/data:/data \
  -v ${STORAGE_DIR}/volume/ssh/authorized_keys:/home/${USER_NAME}/.ssh/authorized_keys \
  -v ${STORAGE_DIR}/volume/ssh/config:/home/${USER_NAME}/.ssh/config \
  -v ${NODE_PATH}/namenode:/opt/volume/namenode \
  -v ${NODE_PATH}/datanode0:/opt/volume/datanode \
  -v ${NODE_PATH}/metastore:/opt/volume/metastore \
  -v ${NODE_PATH}/status:/opt/volume/status \
  -v ${NODE_PATH}/logs:${HADOOP_HOME}/logs \
  -v ${STORAGE_DIR}/hadoop_home/etc/hadoop/core-site-${DC}.xml:${HADOOP_HOME}/etc/hadoop/core-site.xml \
  -v ${STORAGE_DIR}/hadoop_home/etc/hadoop/hdfs-site.xml:${HADOOP_HOME}/etc/hadoop/hdfs-site.xml \
  -v ${STORAGE_DIR}/hive_home/conf/hive-site.xml:${HIVE_HOME}/conf/hive-site.xml \
  -v ${STORAGE_DIR}/docker/run_services.sh:${HADOOP_HOME}/bin/run_services.sh \
  -v ${STORAGE_DIR}/metastore:${HADOOP_HOME}/bin/metastore \
  -v ${ROOT_DIR}:/R23 \
  -w ${HADOOP_HOME} \
  -e HADOOP_HOME=${HADOOP_HOME} \
  -e HIVE_HOME=${HIVE_HOME} \
  -e RUNNING_MODE=${RUNNING_MODE} \
  -e NODE_ID=${NODE_ID} \
  -e USER=${USER_NAME} \
  --network ${BASE_NETWORK_NAME} \
  --name ${BASE_STORAGE_CONTAINER_NAME}-${NODE_ID}  --hostname ${BASE_STORAGE_CONTAINER_NAME}-${NODE_ID} \
  --device /dev/fuse \
  --cap-add SYS_ADMIN \
  --security-opt apparmor:unconfined \
  ${STORAGE_DOCKER_NAME} ${CMD}"

# echo ${DOCKER_RUN}

if [ "$RUNNING_MODE" = "interactive" ]; then
  eval "${DOCKER_RUN}"
else
  eval "${DOCKER_RUN}" &
  while [ ! -f "${NODE_PATH}/status/HADOOP_STATE" ]; do
    sleep 1  
  done

  cat "${NODE_PATH}/status/HADOOP_STATE"
fi

popd

