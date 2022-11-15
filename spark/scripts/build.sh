#!/bin/bash

set -e
#set -x
echo "Building option: [$1]"

# Start fresh, so remove the spark home directory.
echo "Removing $SPARK_HOME"
rm -rf $SPARK_HOME/

# Build Spark
cd $SPARK_SRC
if [ ! -d $SPARK_BUILD ]; then
  echo "Creating Build Directory"
  mkdir $SPARK_BUILD
fi
if [ ! -d $SPARK_HOME ]; then
  echo "Creating SPARK_HOME Directory"
  mkdir $SPARK_HOME
fi

echo "Building spark"
rm $SPARK_SRC/spark-*SNAPSHOT*.tgz || true
./dev/make-distribution.sh --name custom-spark --pip --tgz -Phive
# Install Spark.
# Extract our built package into our install directory.
echo "Extracting $SPARK_PACKAGE.tgz -> $SPARK_HOME"
sudo tar -xzf "$SPARK_SRC/$SPARK_PACKAGE.tgz" -C $SPARK_BUILD \
  && mv $SPARK_BUILD/$SPARK_PACKAGE/* $SPARK_HOME
cp /qflock/conf/*.xml $SPARK_HOME/conf
pushd $SPARK_HOME/python
python setup.py sdist
python3 -mpip install --target $SPARK_HOME/pyspark-3.3.0/ dist/pyspark-3.3.0.tar.gz
popd

pushd $SPARK_HOME/jars
wget https://repo1.maven.org/maven2/javax/json/javax.json-api/1.1.4/javax.json-api-1.1.4.jar
wget https://repo1.maven.org/maven2/org/glassfish/javax.json/1.1.4/javax.json-1.1.4.jar
popd
