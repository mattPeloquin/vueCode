#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Create login env variables
#
#   Can't affect current process with a bash script -- this
#   sets up subsequent processes to have these env variables
#
#       EXPECTS TO RUN WITH ROOT PRIVILEGES
#
#   	CALLED FROM USER BOOTSTRAP BEFORE CODE UPDATE,
#		SO CHANGES MUST BE BAKED INTO AMI
#
#   These items are the only run-time environment items needed
#   to bring up machines in an autoscale instance, as all other
#   persistent config should be set in yaml env config files.
#
#   This script can set up initial AMIs (which bake these
#	values in so they are present for autoscale start) and also
#   to reset server roles in dev/test
#
#   If this is being run in a shell where the items have already
#   been defined, it can take a subset of the parameteres, e.g.,:
#
#       sudo bash deploy/shell/setenv.sh '' '' 'A' 'tip' 'mpextend'
#

env_file=/etc/profile.d/mpframework_env.sh

# Manually import login environment variables; since running as root
source $env_file

# Setup arguments; if blank is passed in, use current value
if [[ "$1" == "" ]]; then
    home_folder=$MP_HOME
else
    home_folder=$1
fi
if [[ "$2" == "" ]]; then
    profile=$MP_PROFILE
else
    profile=$2
fi
if [[ "$3" == "" ]]; then
    tag=$MP_PROFILE_TAG
else
    tag=$3
fi
if [[ "$4" == "" ]]; then
    code_rev=$MP_CODE_REV
else
    code_rev=$4
fi
if [[ "$5" == "" ]]; then
    platforms=$MP_PLATFORMS
else
    platforms=$5
fi

# Create settings and write out to file
echo ""
echo "Current settings:"
echo "   MP_HOME            = "${home_folder}
echo "   MP_PROFILE         = "${profile}
echo "   MP_PROFILE_TAG     = "${tag}
echo "   MP_CODE_REV        = "${code_rev}
echo "   MP_PLATFORMS       = "${platforms}
echo ""

echo "Removing existing environment file: "${env_file}
rm -f $env_file

_env='export MP_PROFILE="'${profile}'"'
_env=$_env';export MP_HOME="'${home_folder}'"'
_env=$_env';export MP_PROFILE_TAG="'${tag}'"'
_env=$_env';export MP_CODE_REV="'${code_rev}'"'
_env=$_env';export MP_PLATFORMS="'${platforms}'"'

echo -e $_env > $env_file

echo ""
echo "New environment file: "${env_file}
cat $env_file
