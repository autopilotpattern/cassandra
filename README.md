# Autopilot Pattern Cassandra


```
cd examples/compose
docker-compose up -d --scale cassandra=3
# for a cqlsh shell:
docker-compose exec cassandra cqlsh cassandra

cqlsh> CREATE KEYSPACE demo WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 2 };
USE demo;

```