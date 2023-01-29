# svn status|grep M|grep -v bidu|awk '{printf("cp %s /home/work/maguannan/tools/apache2/htdocs/plib_cup_opensource/cup/%s\n", $2, $2)}' > /tmp/cmds
find -type d |grep -v .svn |grep -v bidu|grep -v .pyc|awk '{printf("mkdir /home/work/maguannan/tools/apache2/htdocs/plib_cup_opensource/cup/%s\n", $1)}' > ./cmds
find -type f |grep -v .svn |grep -v bidu|grep -v mail.py|grep -v _mysql|grep -v .pyc|grep -v cscope|awk '{printf("cp %s /home/work/maguannan/tools/apache2/htdocs/plib_cup_opensource/cup/%s\n", $1, $1)}' >> /tmp/cmds
cat /tmp/cmds
bash /tmp/cmds
