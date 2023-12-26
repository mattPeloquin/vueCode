#!/bin/bash
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
#
#   Install MPF server environment
#
#   Normally only run when creating server AMI, but is
#   non-destructive if it is run for updating.
#
source $MP_HOME/mpframework/deploy/shell/inc_common.sh

echo -e "\n---------------------------------------------------------"
echo -e "Setting up MPF environment in "$home_folder"\n"
cd $home_folder

echo -e "\n--- Installing package build dependencies"

echo -e "\n-> gcc for building"
$sudo_cmd yum -y install gcc gcc-c++ make

echo -e "\n-> support for building Python3.9"
$sudo_cmd yum -y install bzip2-devel libffi-devel

echo -e "\n-> support for build pycrypto, used by Fabric and Pillow"
$sudo_cmd yum -y install openssl-devel

echo -e "\n-> Support TLS over rsyslog"
$sudo_cmd yum -y install rsyslog-gnutls

echo -e "\n-> YAML C support, must be in place before pip PyYAML installed"
$sudo_cmd yum -y install libyaml-devel

echo -e "\n-> Install nginx from AWS yum extensions"
$sudo_cmd amazon-linux-extras enable nginx1
$sudo_cmd yum -y install nginx

if [[ "$1" == "dev" ]]; then
    echo -e "\n-> Building DEV Sqlite support"
    cd /opt
    # Build sqlite since need later than AL2 package
    $sudo_cmd wget https://www.sqlite.org/2021/sqlite-autoconf-3360000.tar.gz
    $sudo_cmd tar xzf sqlite-autoconf-3360000.tar.gz
    $sudo_cmd rm sqlite-autoconf-3360000.tar.gz
    cd sqlite-autoconf-3360000/
    $sudo_cmd ./configure --enable-optimizations
    $sudo_cmd make install
    # Remove existing
    $sudo_cmd rm -fr /usr/bin/sqlite3
    # The python sqlite library needs to point to new sqlite
    $sudo_cmd yum -y install sqlite-devel
    $sudo_cmd export LD_LIBRARY_PATH="/usr/local/lib"
    $sudo_cmd echo '
export LD_LIBRARY_PATH="/usr/local/lib"
' >> /etc/profile.d/mpframework_env.sh
    cd ~
fi
echo -e "\n-> Adding mySQL"
$sudo_cmd yum -y install mysql mysql-devel

echo -e "\n-> Install Python 3.9 and make default Python"
if [ -d "/usr/local/lib/python3.9" ]; then
    echo -e "\nPython3.9 already installed"
else
    cd /opt
    $sudo_cmd wget https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz
    $sudo_cmd tar xzf Python-3.9.7.tgz
    $sudo_cmd rm Python-3.9.7.tgz
    cd Python-3.9.7/
    $sudo_cmd ./configure --enable-optimizations
    $sudo_cmd make altinstall
    cd ~
fi

echo -e "\n-> Creating virtual environment: "$venv_folder
if [ -d "$venv_folder" ]; then
    echo -e "\nVirtual environment already setup"
else
    python3.9 -m venv $venv_folder

    # Add virtual env to path if not done already
    bash_message="Adding virtual environment path"
    if grep -q "$bash_message" $home_folder/.bashrc; then
        echo -e "\n"$venv_folder" already added to path"
    else
        echo -e "\nAdding "$venv_folder" to path"
        $sudo_cmd echo '
# '"$bash_message"'
PATH=$PATH:'"$venv_folder"'/bin:'"$mp_folder/deploy/shell"'
export PATH
. activate
' >> $home_folder/.bashrc
    fi
fi

. $venv_folder/bin/activate
