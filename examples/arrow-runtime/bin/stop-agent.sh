#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Author: Guannan                                                                                               
# Arguments:                                                                                           
#   None                                                                                               
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
keyword="arrow_agent.py"
masterpid=`ps -ef|grep ${keyword}|grep -v grep|awk '{print $2}'`
echo "try to kill pid ${masterpid}, y or n" 
read answer
if [[ "${answer}" == "y" ]];then
    kill -9 ${masterpid}
    echo "killed"
    ps -ef|grep ${keyword}|grep -v grep
fi
