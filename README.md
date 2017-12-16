# Autopilot Pattern Cassandra

A blueprint for running Apache Cassandra using the [Autopilot Pattern](http://autopilotpattern.io/).

Environment variables:

  - `CASSANDRA_CLUSTER_NAME`: Name of cluster. Cassandra instances can only join a cluster with the
  same `CASSANDRA_CLUSTER_NAME`. Changing this to something other than "Test Cluster"
  is **strongly recommended**.
  - `CASSANDRA_USER`: New user account to create upon cluster initialization. Setting this parameter
  to something other than "cassandra" is **strongly recommended**.
  - `CASSANDRA_PASSWORD`: password for `CASSANDRA_USER`.
  - `CASSANDRA_KEYSPACES`: Comma-seperated list of keyspaces.
  - `CASSANDRA_TOPOLOGY`: JSON map describing keyspaces and their respective datacenters and
    replication factors, e.g. for a cluster deployed with at least 2 nodes in `us-east-1` and
    `us-sw-1` Triton datacenters having a single keyspace named `demo`:
    ```
    { "demo": { "us-sw-1": 2 }, { "us-east-1": 2 } }
    ```

Notes:

```
cd examples/compose
docker-compose up -d --scale cassandra=3
# for a cqlsh shell:
docker-compose exec cassandra cqlsh cassandra

cqlsh> CREATE KEYSPACE demo WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 2 };
USE demo;

```


# Credits

- Minimal Cassandra configuration based on John Berryman's [Building the Perfect Cassandra Test Environment](http://opensourceconnections.com/blog/2013/08/31/building-the-perfect-cassandra-test-environment/)
