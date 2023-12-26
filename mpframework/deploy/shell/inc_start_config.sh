#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Command line configuration information
#
#   This is intended to be included via source command
#   Assumes inc_common.sh has been loaded
#

# The prod vs. dev versions names are used in inc_common.sh to select which config
# to use in the xxx_start variables, and then expanded indirectly

# The Nginx conf file must be used in start and stop, which is main reason
# this file is broken out as an include
nginx_prod=$mp_folder/deploy/nginx/prod.conf
nginx_dev=$mp_folder/deploy/nginx/dev.conf

# uWSGI
uwsgi_config=$mp_folder/deploy/uwsgi_config/uwsgi.yaml
