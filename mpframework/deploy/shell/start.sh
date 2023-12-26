#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Start servers
#
source $MP_HOME/mpframework/deploy/shell/inc_common.sh
source $MP_HOME/mpframework/deploy/shell/inc_start_config.sh


# Setup run commands
# Note the xxx_start variables are setup in the inc_common file
run_rsyslog="$sudo_cmd service rsyslog restart"
run_uwsgi="uwsgi --yaml $uwsgi_config"
run_nginx="$sudo_cmd nginx -c ${!nginx_start}"

# Provide tracking on which config file is being used
echo -e "prod_profile: "$prod_profile
echo -e "\nEnvironment for server start:\n"
env | grep  MP_

echo -e "\n============================================="

# Restart rsyslog to pick up any changes, and display any errors
echo -e "\nRestarting rsyslog logger..."
echo " > "$run_rsyslog
$run_rsyslog

# Start uwsgi next so it is ready to listen for nginx requests
echo -e "\nStarting uWsgi..."
echo " > "$run_uwsgi
$run_uwsgi

# Nginx must run as root because we have to bind to port 80 (anything < 1024 requires root)
echo -e "\nStarting Nginx..."
echo " > "$run_nginx
$run_nginx
