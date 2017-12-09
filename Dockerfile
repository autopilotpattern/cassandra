FROM cassandra:3.11.0

# install wget unzip and dig plus python modules
RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends -y wget unzip dnsutils python-dev gcc \
    && wget --quiet -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py \
    && python /tmp/get-pip.py \
    && pip install \
        # trying to use cqlsh to do this stuff, installing cassandra-driver takes _forever_
        # cassandra-driver==3.12.0 \
        python-Consul==0.7.2 \
        manta==2.6.0 \
        pyyaml==3.12 \
    && apt-get purge -y python-dev gcc \
    && rm /tmp/get-pip.py \
    && rm -rf /var/lib/apt/lists/*

# Install Consul
# Releases at https://releases.hashicorp.com/consul
RUN set -ex \
    && export CONSUL_VERSION=1.0.1 \
    && export CONSUL_CHECKSUM=eac5755a1d19e4b93f6ce30caaf7b3bd8add4557b143890b1c07f5614a667a68 \
    && wget --quiet -O /tmp/consul.zip "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip" \
    && echo "${CONSUL_CHECKSUM}  /tmp/consul.zip" | sha256sum -c \
    && unzip /tmp/consul -d /usr/local/bin \
    && rm /tmp/consul.zip \
    && mkdir -p /etc/consul \
    && mkdir -p /var/lib/consul \
    && mkdir /config

# Install Consul template
# Releases at https://releases.hashicorp.com/consul-template/
RUN set -ex \
    && export CONSUL_TEMPLATE_VERSION=0.19.0 \
    && export CONSUL_TEMPLATE_CHECKSUM=31dda6ebc7bd7712598c6ac0337ce8fd8c533229887bd58e825757af879c5f9f \
    && wget --quiet -O /tmp/consul-template.zip "https://releases.hashicorp.com/consul-template/${CONSUL_TEMPLATE_VERSION}/consul-template_${CONSUL_TEMPLATE_VERSION}_linux_amd64.zip" \
    && echo "${CONSUL_TEMPLATE_CHECKSUM}  /tmp/consul-template.zip" | sha256sum -c \
    && unzip /tmp/consul-template.zip -d /usr/local/bin \
    && rm /tmp/consul-template.zip

# Add Containerpilot and set its configuration
ENV CONTAINERPILOT /etc/containerpilot.json5
ENV CONTAINERPILOT_VERSION 3.6.1

RUN export CONTAINERPILOT_CHECKSUM=57857530356708e9e8672d133b3126511fb785ab \
    && export archive=containerpilot-${CONTAINERPILOT_VERSION}.tar.gz \
    && wget --quiet -O /tmp/${archive} \
         "https://github.com/joyent/containerpilot/releases/download/${CONTAINERPILOT_VERSION}/${archive}" \
    && echo "${CONTAINERPILOT_CHECKSUM}  /tmp/${archive}" | sha1sum -c \
    && tar zxf /tmp/${archive} -C /usr/local/bin \
    && rm /tmp/${archive}

COPY etc/containerpilot.json5 /etc/containerpilot.json5

### Cassandra-specific setup follows

COPY etc/containerpilot_handler /usr/local/bin/containerpilot_handler
COPY etc/containerpilot_handler.py /usr/local/bin/containerpilot_handler.py
COPY etc/cassandra.yaml.ctmpl /etc/cassandra/cassandra.yaml.ctmpl

# disable the automatic seed configuration that enables single-node bootstrapping
# the first line corresponds to "always set self as seed"
# the second line actually inserts CASSANDRA_SEEDS into the cassandra.yaml
RUN sed -ri '/CASSANDRA_SEEDS.*CASSANDRA_BROADCAST_ADDRESS/d' /docker-entrypoint.sh && \
    sed -ri '/sed -ri.*CASSANDRA_SEEDS.*\/cassandra.yaml/d' /docker-entrypoint.sh


EXPOSE 7000 7001 7199 9042 9160

ENTRYPOINT ["/usr/local/bin/containerpilot"]
