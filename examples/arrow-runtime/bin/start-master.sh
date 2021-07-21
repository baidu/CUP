#!/bin/bash

export PYTHONPATH=`pwd`/../../:${PYTHONPATH}:`pwd`/

cd ./arrow/master/; nohup python ./arrow_master.py ./conf/master.conf >../../log/master.stdout.stderr &
# cd ./arrow/master/; nohup pypy ./arrow_master.py ./conf/master.conf >../../log/master.stdout.stderr &

