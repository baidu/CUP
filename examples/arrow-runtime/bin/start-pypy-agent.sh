#!/bin/bash

export PYTHONPATH=`pwd`/:${PYTHONPATH}

cd ./arrow/agent/; nohup pypy ./arrow_agent.py ./conf/agent.conf >../../log/agent.stdout.stderr &

