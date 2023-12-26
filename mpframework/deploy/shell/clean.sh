#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Reset local files on a server
#   This should only be run when server processes are stopped
#
source $MP_HOME/mpframework/deploy/shell/inc_common.sh

echo "Cleaning temporary files"

# Clear out python object files from everywhere
sudo find $home_folder -type f -name "*.pyc" -exec rm -f {} \;
sudo find $home_folder -type f -name "*.pyo" -exec rm -f {} \;

# Reset temp files and logs (nginx, uwsgi, and local work)
sudo rm -fr $nginx_folder
sudo rm -fr $uwsgi_folder
sudo rm -fr $local_work_folder

# Reset Cloud-init logs
sudo rm -f /var/log/cloud-init.log
