#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Author:                                                                                              
# Date:                                                                                                
# Brief:                                                                                               
#                                                                                                      
# Arguments:                                                                                           
#   None                                                                                               
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
find . -name '*.html' -print0 | xargs -0 sed -i "" "s/@baidu.com//g"
