#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Author: Guannan Ma                                                                                              
# Brief:  Upload cup to pypi                                                                                             
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
bash ./clean_build.sh
python setup.py bdist_wheel
twine upload  ./output/dist/*
