#!/bin/bash
set -e
pushd "$(dirname "$0")"
ROOT_DIR=$(git rev-parse --show-toplevel)
SPARK_DIR=$ROOT_DIR/spark
SCRIPTS_DIR=$ROOT_DIR/scripts
source $ROOT_DIR/scripts/spark/spark_version
echo "build_spark.sh: SPARK_VERSION $SPARK_VERSION"

if [ ! -d $SPARK_DIR/build ]; then
  mkdir $SPARK_DIR/conf | true
  source $SPARK_DIR/docker/setup_build.sh
fi

# Include the setup for our cached local directories. (.m2, .ivy2, etc)
source $SPARK_DIR/docker/setup.sh

if [[ "$1" == "-d" ]]; then
  echo "Starting build docker."
  DOCKER_NAME="spark_build_debug"
  shift

  docker run --rm -it --name $DOCKER_NAME \
  --network qflock-net-dc1 \
  --mount type=bind,source=$ROOT_DIR,target=/qflock \
  --mount type=bind,source=$SPARK_DIR/spark,target=/spark \
  --mount type=bind,source=$SPARK_DIR/extensions/,target=/extensions \
  --mount type=bind,source=$SPARK_DIR/build,target=/build \
  --mount type=bind,source=$SPARK_DIR/scripts,target=/scripts \
  --entrypoint /bin/bash -w /spark \
  -v ${SPARK_DIR}/build/.m2:${DOCKER_HOME_DIR}/.m2 \
  -v ${SPARK_DIR}/build/.gnupg:${DOCKER_HOME_DIR}/.gnupg \
  -v ${SPARK_DIR}/build/.sbt:${DOCKER_HOME_DIR}/.sbt \
  -v ${SPARK_DIR}/build/.cache:${DOCKER_HOME_DIR}/.cache \
  -v ${SPARK_DIR}/build/.ivy2:${DOCKER_HOME_DIR}/.ivy2 \
  -u "${USER_ID}" \
  $SPARK_DOCKER_NAME $@
else
  echo "Starting build for $@"

  docker run --rm -it --name spark_build \
  --network qflock-net-dc1 \
  --mount type=bind,source=$ROOT_DIR,target=/qflock \
  --mount type=bind,source=$SPARK_DIR/spark,target=/spark \
  --mount type=bind,source=$SPARK_DIR/extensions/,target=/extensions \
  --mount type=bind,source=$SPARK_DIR/build,target=/build \
  --mount type=bind,source=$SPARK_DIR/scripts,target=/scripts \
  --entrypoint /bin/bash -w /spark \
  -v ${SPARK_DIR}/build/.m2:${DOCKER_HOME_DIR}/.m2 \
  -v ${SPARK_DIR}/build/.gnupg:${DOCKER_HOME_DIR}/.gnupg \
  -v ${SPARK_DIR}/build/.sbt:${DOCKER_HOME_DIR}/.sbt \
  -v ${SPARK_DIR}/build/.cache:${DOCKER_HOME_DIR}/.cache \
  -v ${SPARK_DIR}/build/.ivy2:${DOCKER_HOME_DIR}/.ivy2 \
  -u "${USER_ID}" \
  $SPARK_DOCKER_NAME /scripts/build.sh spark
fi