#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Common Library
#
#   Intended to be included with via:
#
#       source $MP_HOME/mpframework/deploy/shell/inc_common.sh
#
#   which should be the only hard-coded path in any shell file; all
#   other paths should be derived from variables here
#
#   	CALLED FROM USER DATA BOOTSTRAP BEFORE CODE UPDATE,
#		SO CHANGES MAY NEED TO BE BAKED INTO AMI
#

# Some scripts can run both from shells and bootstrap (which runs from root)
# so need to check if running as root (the $EUID check)
# If already running as root need to manually install key
# environment variables (because they are only loaded for ec2-user)
# Also set up a prefix to not call sudo in scripts if already root
if [[ $EUID == 0 ]]; then
    sudo_cmd=
    source /etc/profile.d/mpframework_env.sh
else
    sudo_cmd=sudo
fi

# --------------------------------------------------------------
# Folder setup

# Refernce $MP_HOME as the home folder becuase AWS Linux
# sets $HOME to root when running sudo -E
home_folder=$MP_HOME

venv_folder=$home_folder/.venv

# Fixed folders deployed and managed in the root
mp_folder=$home_folder/mpframework
nginx_folder=$home_folder/nginx
uwsgi_folder=$home_folder/uwsgi
local_work_folder=$home_folder/.work

# Array of all folders to create and manage permissions on
managed_folders=( "$local_work_folder" )
managed_folders=( "${managed_folders[@]}" "$nginx_folder" )
managed_folders=( "${managed_folders[@]}" "$uwsgi_folder $uwsgi_folder/spooler" )

# --------------------------------------------------------------
# Setup config settings based on profile

# Is this a production environment?
if [[ "$MP_PROFILE" == prod* ]]; then
    prod_profile=true
else
    prod_profile=false
fi

# Select nginx config files based on profile
# This logic is here because some config used to run services needs to be
# accessed in start and stop. Note using indirect expansion of the
# variables in question; so they are being selected here, but their
# values are defined elsewhere
if $prod_profile ; then
    nginx_start=nginx_prod
else
    nginx_start=nginx_dev
fi
