#
# Setup a DEV container
# NOT A PRODUCTION MPF CONTAINER
# Mimics low-cost VM deployment so is not an optimized container.
# FUTURE - create separate nginx and uwsgi containers for K8s
#
FROM amazonlinux

ARG user=ec2-user
ARG home=/home/ec2-user
ARG scripts=/mpframework/deploy/shell

EXPOSE 80

# Amazon linux container not set to UTF8 like regular image
ENV LC_ALL en_US.UTF-8

RUN yum -y update && yum -y install \
    wget \
    tar \
    # Add Linux user tools
    sudo \
    shadow-utils

# Run as ec2-user to emulate VM
RUN groupadd -g 1000 ${user} && \
    useradd -u 1000 -g ${user} -G wheel -m ${user} && \
    usermod -p "" ${user}

# Perform server setup baked into AMI
COPY --chown=ec2-user:ec2-user .${scripts} ${home}${scripts}
ENV MP_HOME=${home}
RUN ${home}${scripts}/setenv.sh ${home}
RUN ${home}${scripts}/install_server.sh dev

# Copy code subset before pip to optimize build caching
COPY --chown=ec2-user:ec2-user ./*.py ${home}
COPY --chown=ec2-user:ec2-user ./mpframework/deploy ${home}/mpframework/deploy
COPY --chown=ec2-user:ec2-user ./mpframework/common ${home}/mpframework/common
COPY --chown=ec2-user:ec2-user ./mpextend/deploy ${home}/mpextend/deploy
COPY --chown=ec2-user:ec2-user ./vueocity/deploy ${home}/vueocity/deploy

# Setup venv and bootstrap enough to call fabric
ENV PATH="${home}/.venv/bin:${PATH}"
WORKDIR ${home}
RUN . activate && \
   pip install fabric wrapt

RUN fab update-pip

COPY --chown=ec2-user:ec2-user . ${home}

USER ${user}
ENV LD_LIBRARY_PATH="/usr/local/lib"

RUN fab update-dirs
RUN fab db-sync
RUN fab db-load
RUN fab server-config
RUN fab static

ENV MP_LOG_LEVEL_DEBUG_MIN=1

CMD /home/ec2-user/mpframework/deploy/shell/start.sh ; /bin/bash
