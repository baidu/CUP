#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Author: Guannan @mythmgn
# Brief:                                                                                               
#   a. Diff changes between github repo and baidu internal repo                                                                                                     
#   b. Commit changes of a to heading repo.
# Arguments:                                                                                           
#   None                                                                                               
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
diff_opts=" -c "


bidu_cup_dir="./cup/"
github_dir="../../../open-source/python/cup_on_github/"
exclude_diffs="cup_thirdp .git bidu diff.sh gendoc.sh"
cmds="find ${bidu_cup_dir} -type f"

for ex in ${exclude_diffs}
do
    cmds="${cmds}|grep -v ${ex}"
done
lines=`eval ${cmds}`

for line in ${lines}
do
    diff ${diff_opts} ${line} ${github_dir}${line}
    if [[ $? -ne 0 ]];then
        # echo "---${line} vs ${github_dir}${line}--"
        echo "----------------------------------------------------------------"
    fi
done

