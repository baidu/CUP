#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Brief: Generate new xxx.rst files for build api-ref doc                                                                                              
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
export PYTHONPATH=`pwd`:`pwd`/src:$PYTHONPATH
DOC_VERSION=`cat pyproject.toml |grep version|awk '{print $3}'|tr -d "\""`
sphinx-apidoc -F   --module-first -o `pwd`/newdoc  --doc-version ${DOC_VERSION} --ext-todo   --doc-author "CUP-DEV Team" cup bidu
cd newdoc && make html && cd -
echo "to delete ./docs/api-ref"
rm -rf ./docs/api-ref/*
cp -r ./newdoc/_build/html/* ./docs/api-ref/
