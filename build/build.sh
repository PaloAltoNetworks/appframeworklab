#!/bin/bash
echo "Checking if CONF bucket has changed..."
if [[ "$BCONF" == "0" ]]; then
  git diff-tree --quiet HEAD HEAD^ -r buckets/appframework-conf || BCONF=1
fi
if [[ "$BCONF" == "1" ]]; then
  echo "CONF bucket has changed, regenerating ZIP file..."
  zip -r buckets/appframework-conf.zip buckets/appframework-conf
fi

