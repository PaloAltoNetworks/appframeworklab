#!/bin/bash
echo "Checking if NGFW bucket has changed..."
BNGFW=0
git diff-tree --quiet HEAD HEAD^ -r buckets/appframework-ngfw || BNGFW=1
if [[ "$BNGFW" == "1" ]]; then
  echo "NGFW bucket has changed, regenerating ZIP file..."
  echo zip -r buckets/appframework-ngfw.zip buckets/appframework-ngfw
fi

BRES=0
echo "Checking if resources have changed..."
git diff-tree --quiet HEAD HEAD^ -r resources || BRES=1
if [[ "$BRES" == "1" ]]; then
  echo "Resources have changed, regenerating TAR.GZ file..."
  echo tar cvfz buckets/appframework-conf/opt/apiexplorer.tar.gz resources
  BCONF=1
else
  BCONF=0
fi

echo "Checking if CONF bucket has changed..."
if [[ "$BCONF" == "0" ]]; then
  git diff-tree --quiet HEAD HEAD^ -r buckets/appframework-ngfw || BCONF=1
fi
if [[ "$BCONF" == "1" ]]; then
  echo "CONF bucket has changed, regenerating ZIP file..."
  echo zip -r buckets/appframework-conf.zip buckets/appframework-conf
fi

