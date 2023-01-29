#!/bin/bash

set -e # exit on error

rm -f /opt/volume/status/HADOOP_STATE

if [ ! -f /opt/volume/namenode/current/VERSION ]; then
    if [ ${NODE_ID} == "0" ]; then
        "${HADOOP_HOME}/bin/hdfs" namenode -format
    fi
    # $HIVE_HOME/bin/schematool -dbType derby -initSchema
fi

# Start ssh service
sudo service ssh start

export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HADOOP_HOME/lib/native


if [ ${NODE_ID} == "0" ]; then # Start HDFS on node 0 only, later we will start datanodes on other storage nodes
    echo "Starting Name Node ..."
    "${HADOOP_HOME}/bin/hdfs" --daemon start namenode

    echo "Starting Data Node ..."
    "${HADOOP_HOME}/bin/hdfs" --daemon start datanode
fi


export CLASSPATH=$(bin/hadoop classpath)
sleep 1

if [ ${NODE_ID} == "0" ]; then # Start Metastore on node 0 only
    python3 ${HADOOP_HOME}/bin/metastore/qflock_metastore_server.py &
fi

if [ ${NODE_ID} == "0" ]; then # Start stats_server on node 0 only
    pushd /R23/spark/spark_changes/scripts/stats_server
    python3 stats_server.py &
    popd
fi 

# Check if orangefs directory exists
if [ ! -d /opt/volume/filesystem/orangefs ]; then
    mkdir -p /opt/volume/filesystem/orangefs
    mkdir -p /opt/volume/filesystem/orangefs/data
    mkdir -p /opt/volume/filesystem/orangefs/logs
fi

echo "HADOOP_READY"
echo "HADOOP_READY" > /opt/volume/status/HADOOP_STATE

echo "RUNNING_MODE $RUNNING_MODE"

if [ "$RUNNING_MODE" = "daemon" ]; then
    sleep infinity
fi