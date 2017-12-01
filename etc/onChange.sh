#!bin/sh
consul-template -once -template /etc/cassandra/cassandra.yaml.ctmpl:/etc/cassandra/cassandra.yaml

nodetool -u cassandra -pw cassandra stopdaemon

# TODO: dont stopdaemon unless there are enough other nodes available
# if [ $((`nodetool -u cassandra -pw cassandra status | grep -v $HOSTNAME | grep UN | wc -l`)) -gt 1 ]; then
#   nodetool -u cassandra -pw cassandra stopdaemon
# fi

