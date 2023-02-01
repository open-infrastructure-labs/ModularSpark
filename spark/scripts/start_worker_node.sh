#!/bin/bash
ROOT_DIR=$(git rev-parse --show-toplevel)
source ${ROOT_DIR}/version

# source $ROOT_DIR/scripts/spark/spark_version
# source docker/setup.sh
USER_NAME=${SUDO_USER:=$USER}

# We may choose to relocate this script to it's own ${ROOT_DIR}/worker directory
WORKER_DIR=${ROOT_DIR}/spark

# Set the home directory in the Docker container.
DOCKER_HOME_DIR=${DOCKER_HOME_DIR:-/home/${USER_NAME}}

RUNNING_MODE="daemon"
NODE_ID=0 # set default node_id

VALID_ARGS=$(getopt -o i:,c: --longoptions node_id:,cmd: -- "$@")
if [[ $? -ne 0 ]]; then
    exit 1;
fi

NODE_ID=0 # set default node_id
CMD="/usr/local/bin/run_services.sh" # set default command to run worker services
RUNNING_MODE="daemon"

eval set -- "$VALID_ARGS"
while [ : ]; do  
  case "$1" in
    -i | --node_id)
        echo "node_id = $2"
        NODE_ID=$2
        shift
        ;;
    -c | --cmd)
        echo "cmd = $2"
        CMD=$2
        RUNNING_MODE="interactive"
        shift
        ;;        
    --)
      break
      ;;
  esac
  shift
done


NODE_PATH=${WORKER_DIR}/volume/node-${NODE_ID}
mkdir -p "${NODE_PATH}/status"
rm -f "${NODE_PATH}/status/WORKER*"

mkdir -p "${NODE_PATH}/logs"

mkdir -p "${NODE_PATH}/spark/logs"
rm -f "${NODE_PATH}/spark/logs/worker*.log"

if [ $RUNNING_MODE = "interactive" ]; then
  DOCKER_IT="-i -t"
fi

SPARK_DIR=${ROOT_DIR}/spark
SPARK_WORKER_CONFIG="--expose 7012 --expose 7013 --expose 7014 --expose 7015 --expose 8881 \
  -e MASTER=spark://sparkmaster:7077 \
  -e SPARK_CONF_DIR=/conf \
  -e SPARK_PUBLIC_DNS=localhost \
  -e SPARK_LOG_DIR=/opt/volume/logs \
  -e HADOOP_CONF_DIR=/build/spark-$SPARK_VERSION/conf \
  --mount type=bind,source=$ROOT_DIR,target=/qflock \
  --mount type=bind,source=$SPARK_DIR/spark,target=/spark \
  --mount type=bind,source=$SPARK_DIR/build,target=/build \
  --mount type=bind,source=$SPARK_DIR/extensions/,target=/extensions \
  -v ${SPARK_DIR}/volume/metastore:/opt/volume/metastore \
  -v ${SPARK_DIR}/volume/user/hive:/user/hive \
  -v ${SPARK_DIR}/build/.m2:${DOCKER_HOME_DIR}/.m2 \
  -v ${SPARK_DIR}/build/.gnupg:${DOCKER_HOME_DIR}/.gnupg \
  -v ${SPARK_DIR}/build/.sbt:${DOCKER_HOME_DIR}/.sbt \
  -v ${SPARK_DIR}/build/.cache:${DOCKER_HOME_DIR}/.cache \
  -v ${SPARK_DIR}/build/.ivy2:${DOCKER_HOME_DIR}/.ivy2 \
  -v ${SPARK_DIR}/bin/:${DOCKER_HOME_DIR}/bin "

DOCKER_RUN="docker run ${DOCKER_IT} --rm -p 8081:8081 \
  --name ${WORKER_CONTAINER_NAME}-${NODE_ID} \
  --network ${BASE_NETWORK_NAME} \
  ${SPARK_WORKER_CONFIG} \
  -v ${WORKER_DIR}/docker/run_services.sh:/usr/local/bin/run_services.sh \
  -v ${NODE_PATH}/status:/opt/volume/status \
  -v ${NODE_PATH}/logs:/opt/volume/logs \
  -v ${ROOT_DIR}/filesystem:/R23/filesystem \
  -e RUNNING_MODE=${RUNNING_MODE} \
  -e NODE_ID=${NODE_ID} \
  -e USER=${USER_NAME} \
  --device /dev/fuse \
  --security-opt apparmor:unconfined \
  --cap-add SYS_ADMIN \
  ${WORKER_DOCKER_NAME}-${USER_NAME} ${CMD}"

echo ${DOCKER_RUN}

if [ $RUNNING_MODE = "interactive" ]; then
  eval "${DOCKER_RUN}"
else
  eval "${DOCKER_RUN}" &
  while [ ! -f "${NODE_PATH}/status/WORKER_STATE" ]; do
    sleep 1
  done

  cat "${NODE_PATH}/status/WORKER_STATE"
fi

