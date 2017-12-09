#!/usr/bin/env python
from __future__ import print_function
from time import sleep
from sys import argv, stderr, path
from consul import Consul
from socket import gethostname
from os.path import exists, isdir

from containerpilot_handler.cassandra import Cassandra
from containerpilot_handler.utils import resolve_home, resolve_cluster_name, resolve_credentials, resolve_datacenter, resolve_storage, await_leader, log


def main(args):
  log('containerpilot_handler started: {}'.format(str(args)))

  CASSANDRA_HOME = resolve_home()
  CASSANDRA_USER, CASSANDRA_PASSWORD = resolve_credentials()
  consul = Consul()
  CASSANDRA_DC = resolve_datacenter(consul)

  storage = resolve_storage()

  await_leader(consul)

  node = Cassandra(consul, storage, CASSANDRA_HOME, CASSANDRA_USER, CASSANDRA_PASSWORD, CASSANDRA_DC, resolve_cluster_name())

  log('node configuration: {}'.format(node))

  current_seeds = node.query_seeds()

  if 'fakeBoot' in args:
    log('pretending to boot')
    sleep(10)
    log('fakeBoot complete')
    return


  if 'preStart' in args:
    # loop while we try to grab a lock on the seeds list
    while not node.enough_seeds_exist(current_seeds) and not node.register_as_seed(current_seeds):
      sleep(5)
      current_seeds = node.query_seeds()
      log('waiting for seeds lock, current seed list: {}'.format(str(current_seeds)))

    # either enough seed nodes appeared in consul kv or we managed to add ourselves and grab the lock

    # render our template in case there are existing seeds
    log('rendering configuration during preStart')

    # attempting to render the config immediately can result in our own volunteering being omitted
    # TODO: figure out what consul-template config would work like this (and not block indefinitely)
    sleep(1)

    node.render_config()

    # create a lock to track our snapshots
    if node.storage is None:
      log('no storage configured, skipping snapshots')
    else:
      _, snapshot_lock = consul.kv.get(node.build_snapshot_key())
      if snapshot_lock is None:
        log('FLAG_SNAPSHOT_REQUIRED was missing')
        snapshot_set = consul.kv.put(node.build_snapshot_key(), Cassandra.FLAG_SNAPSHOT_REQUIRED, acquire=node.session_id)
        if not snapshot_set:
          raise ValueError('error occurred while setting FLAG_SNAPSHOT_REQUIRED')
        else:
          log('FLAG_SNAPSHOT_REQUIRED recorded for {}'.format(node.id))

    log('preStart complete')
    return

  if 'onChange' in args:

    if node.storage is None:
      log('no storage configured, skipping snapshots')
    else:
      tag = node.record_snapshots()
      snapshot_dirs = ['{}/data/{}/snapshots/{}'.format(node.home, k, tag) for k in node.list_keyspaces()]
      
      log('snapshot dirs: {}'.format(str(snapshot_dirs)))

      for d in snapshot_dirs:
        if not isdir(d):
          log('snapshot directory missing: {}'.format(d))

    # snapshot_state = node.query_snapshot_state()
    # log('snapshot state: {}'.format(snapshot_state))

    # if snapshot_state is None or snapshot_state == Cassandra.FLAG_SNAPSHOT_REQUIRED:
    #   log('recording snapshot')
    #   # node.record_snapshots()
    #   # node.ship_snapshots()

    log('onChange complete')
    return


# snapshot_available = node.query_snapshot_state()


# current_peers = node.query_peers()


# # TODO: dont stopdaemon unless there are enough other nodes available
# # if [ $((`nodetool -u cassandra -pw cassandra status | grep -v $HOSTNAME | grep UN | wc -l`)) -gt 1 ]; then
# #   nodetool -u cassandra -pw cassandra stopdaemon
# # fi

# https://stackoverflow.com/questions/6323860/sibling-package-imports
# Ugly hack to allow absolute import from the root folder
# whatever its name is. Please forgive the heresy.
if __name__ == "__main__":
  main(argv[1:])