answer="n"
PATHFILE=./data/TOPDIR
if [ -e  ${PATHFILE} ];then
    TOPDIR=`cat ./data/TOPDIR`
    echo "plz confirm if TOPDIR of arrow is ${TOPDIR}, enter y"
    read answer
fi

if [[ ${answer} != "y" ]];then
    echo "plz specify homedir of arrow"
    read TOPDIR
    echo ${TOPDIR} > ${PATHFILE}
fi

echo "TOPDIR of arrow is ${TOPDIR}"


export PYTHONPATH=${TOPDIR}/../../:${TOPDIR}:$PYTHONPATH
