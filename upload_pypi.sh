#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Author: Guannan Ma                                                                                              
# Brief:  Upload cup to pypi                                                                                             
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
rm -rf ./build ./cup.egg-info ./dist
python setup.py bdist_wheel
twine upload  dist/*
