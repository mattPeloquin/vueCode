#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Install folders and permissions
#
source $MP_HOME/mpframework/deploy/shell/inc_common.sh


echo "Creating mpFramework folders"

for folder in "${managed_folders[@]}"
do
    echo "   " $folder
    $sudo_cmd su ec2-user -p -c "mkdir -p $folder"
done
