#! /bin/bash

# The purpose of this script is to automatically find and replace any config files which are using
# a specific repo name and version (BASE_PREFIX).
# After running this script, it is necessary to change both the repo name and version number
# in the top level version file.

set -e # exit on error
ROOT_DIR=$(git rev-parse --show-toplevel)
pushd "$ROOT_DIR" # connect to root
source version

if [ "$#" -ne 1 ]; then
  echo "$0: new prefix parameter missing."
  exit 1
fi

# grep -r "modular-spark" --exclude=\*.json --exclude="*previous" --exclude="*export" \
#      --exclude="*out" --exclude="*.log" --exclude="*.txt" --exclude="*.lock" --exclude="*.csv"
NEW_PREFIX=$1
echo "old prefix: $BASE_PREFIX new prefix: $NEW_PREFIX"
read -p "Continue? (Y/N): " confirm
echo $confirm

if [ "$confirm" == "Y" ]; then
    echo "replacing $BASE_PREFIX with $NEW_PREFIX"
    find . -not -path "*scripts/find_repo_matches.sh*" \
            \( -name "*.yaml" -o -name "*.xml" -o -name "*.sh" -o -name "*.py" \) -type f \
            | xargs -d '\n' grep -l "foo" \
            | xargs sed -i "s/foo/$NEW_PREFIX/g"
else
  echo "Not replacing prefix."
fi