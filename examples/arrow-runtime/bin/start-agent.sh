#!/bin/bash

export PYTHONPATH=`pwd`/:${PYTHONPATH}:`pwd`/../../

cd ./arrow/agent/; nohup python ./arrow_agent.py ../../conf/agent.conf </dev/null >../../log/agent.stdout.stderr &
