#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Update file permissions
#
#   Permissions can get out of whack in various ways including updates,
#   so set/reset everything here.
#
#	HACK -- udating permissions like this is ugly
#   One reason is root user gets used sometimes. It would be nice to sort
#   out and prevent the places where permissions get messed up, but
#   is compicated by external tools.
#	So ensuring return to a known good state works.
#
source $MP_HOME/mpframework/deploy/shell/inc_common.sh

echo "Setting permissions for top level folders"
for folder in "${managed_folders[@]}"
do
    echo "   " $folder

    # Take away some file permissions
    $sudo_cmd chmod -R ug-x $folder
    $sudo_cmd chmod -R o-rwx $folder

    # Add execute privileges on folders
    $sudo_cmd chmod -R ug+X $folder

    # Add read/write for files
    $sudo_cmd chmod -R ug+rw $folder

done

echo "Setting permissions for nginx var/lib folder"
$sudo_cmd chown -R ec2-user:ec2-user /var/lib/nginx
$sudo_cmd chmod -R ug+rw /var/lib/nginx
