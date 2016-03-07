#!/bin/bash

if [ -e ./output ];then
    rm -rf ./output
fi
mkdir ./output/
cd output
svn export https://svn.baidu.com/inf-test/ds/trunk/pylib/cup ./cup
svn export https://svn.baidu.com/inf-test/ds/trunk/pylib/setup.py ./setup.py
echo "success"
