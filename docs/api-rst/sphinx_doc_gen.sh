#!/bin/bash                                                                                                                                                                                                   
# ##########################################################################                           
# Brief: Generate new xxx.rst files for build api-ref doc                                                                                              
#                                                                                                      
# Returns:                                                                                             
#   succ: 0                                                                                            
#   fail: not 0                                                                                        
# ##########################################################################   
TOPPATH=`pwd`/../..
export PYTHONPATH=${TOPPATH}/src:$PYTHONPATH
DOC_VERSION=`cat ${TOPPATH}/pyproject.toml |grep version|awk '{print $3}'|tr -d "\""`
SPHINX_EXTENTIONS_OPTS=" --extensions sphinx.ext.autosummary"
sphinx-apidoc -F   --module-first -o ${TOPPATH}/docs/api-rst/newdoc  --doc-version ${DOC_VERSION} ${SPHINX_EXTENTIONS_OPTS}  --doc-author "CUP-DEV Team" ${TOPPATH}/src/cup 
cd newdoc && make html && cd -
echo "to delete ./docs/api-ref"
rm -rf ${TOPPATH}/docs/api-ref/*
cp -r ./newdoc/_build/html/* ${TOPPATH}/docs/api-ref/
