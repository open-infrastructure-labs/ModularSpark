set -e
WORKING_DIR=$(pwd)
ROOT_DIR=$(git rev-parse --show-toplevel)
echo "ROOT_DIR $ROOT_DIR"
echo "WORKING_DIR $WORKING_DIR"

source $ROOT_DIR/version
echo "${REPO_NAME} VERSION: ${REPO_VERSION}"

HADOOP_VERSION="2.7.4"
HADOOP_PACKAGE_URL="https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz"
HADOOP_PACKAGE="hadoop-${HADOOP_VERSION}.tar.gz"
HADOOP_DIR="hadoop-${HADOOP_VERSION}"
USER_NAME=${SUDO_USER:=$USER}
USER_ID=$(id -u "${USER_NAME}")

SPARK_DOCKER_BASE_NAME="${BASE_DOCKER_NAME}"
SPARK_DOCKER_NAME="${SPARK_DOCKER_BASE_NAME}-${USER_NAME}"

# Set the home directory in the Docker container.
DOCKER_HOME_DIR=${DOCKER_HOME_DIR:-/home/${USER_NAME}}

#If this env variable is empty, docker will be started
# in non interactive mode
DOCKER_INTERACTIVE_RUN=${DOCKER_INTERACTIVE_RUN-"-i -t"}

echo "Successfully included setup.sh"