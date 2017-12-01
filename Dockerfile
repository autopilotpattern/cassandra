FROM cassandra:3.11.0

# install wget unzip and dig
RUN set -ex \
    && apt-get update \
    && apt-get install -y wget unzip dnsutils \
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
ENV CONTAINERPILOT_VERSION 3.3.3

RUN export CONTAINERPILOT_CHECKSUM=8d680939a8a5c8b27e764d55a78f5e3ae7b42ef4 \
    && export archive=containerpilot-${CONTAINERPILOT_VERSION}.tar.gz \
    && wget --quiet -O /tmp/${archive} \
         "https://github.com/joyent/containerpilot/releases/download/${CONTAINERPILOT_VERSION}/${archive}" \
    && echo "${CONTAINERPILOT_CHECKSUM}  /tmp/${archive}" | sha1sum -c \
    && tar zxf /tmp/${archive} -C /usr/local/bin \
    && rm /tmp/${archive}

COPY etc/containerpilot.json5 /etc/containerpilot.json5

COPY etc/preStart.sh /etc/preStart.sh
COPY etc/onChange.sh /etc/onChange.sh
COPY etc/cassandra.yaml.ctmpl /etc/cassandra/cassandra.yaml.ctmpl

### Cassandra-specific setup follows

ENV LOCAL_JMX=no

# only the access line actually seems to do anything
RUN echo 'if [ "$LOCAL_JMX" = "no" ]; then' "\n" \
           'JVM_OPTS="$JVM_OPTS -Dcom.sun.management.jmxremote.authenticate=true"' "\n" \
           'JVM_OPTS="$JVM_OPTS -Dcom.sun.management.jmxremote.password.file=/etc/cassandra/jmxremote.password"' "\n" \
           'JVM_OPTS="$JVM_OPTS -Dcom.sun.management.jmxremote.access.file=/etc/cassandra/jmxremote.access"' "\n" \
         'fi' "\n" >> /etc/cassandra/cassandra-env.sh

COPY etc/jmxremote.password /etc/cassandra/jmxremote.password
COPY etc/jmxremote.access /etc/cassandra/jmxremote.access

RUN chown cassandra:cassandra /etc/cassandra/jmxremote.password /etc/cassandra/jmxremote.access \
    && chmod 400 /etc/cassandra/jmxremote.access /etc/cassandra/jmxremote.password \
    && chmod +x /etc/preStart.sh /etc/onChange.sh

EXPOSE 7000 7001 7199 9042 9160

ENTRYPOINT ["/usr/local/bin/containerpilot"]
