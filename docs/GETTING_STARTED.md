# Download build dependencies
```shell
sudo apt-get update
sudo apt-get install curl git docker.io build-essential bison flex
```

# Clone repository
```shell
git submodule  init
git submodule update --recursive --progress
```

# build
```shell
./build.sh
```
# start
```shell
./start.sh
```
# stop
```shell
./stop.sh
```
# clean<BR>
to clean out build artifacts
```shell
./clean.sh
```
# clean all<BR>
cleans out build artifacts and all other artifacts including dockers and downloads
```shell
./clean_all.sh
```
# clean all but skip docker removal
```shell
NO_CLEAN_DOCKERS=1 ./clean_all.sh
```
