#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Brief: Generate new xxx.rst files for build api-ref doc                                                                                              
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
DOC_VERSION=3.2.19
sphinx-apidoc -F   --module-first -o `pwd`/newdoc  --doc-version ${DOC_VERSION} --ext-todo   --doc-author "CUP-DEV Team" cup bidu
