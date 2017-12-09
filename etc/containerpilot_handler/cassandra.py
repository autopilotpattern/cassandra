from __future__ import print_function
from os.path import exists
from sys import stderr
from socket import gethostname, gethostbyname
from datetime import datetime
from containerpilot_handler.utils import log
import yaml
from subprocess import check_output, check_call, STDOUT, PIPE, CalledProcessError

class Cassandra(object):

  FLAG_SNAPSHOT_REQUIRED = 'SNAPSHOT_REQUIRED'

  FILE_SESSION_ID = '/tmp/consul.session'

  def __init__(self, consul, storage, home, user, password, datacenter, cluster_name):
    self.id = "cassandra-{}".format(gethostname())
    self.consul = consul
    self.storage = storage
    self.home = home
    self.user = user
    self.password = password
    self.datacenter = datacenter
    self.cluster_name = cluster_name

    self.session_id = self.load_or_create_session()
    self.persist_session()

  def __str__(self):
    return 'Cassandra <id={}, consul={}, storage={}, user={}, datacenter={}, cluster_name={} session_id={}>'.format(
        self.id, self.consul, self.storage, self.user, self.datacenter, self.cluster_name, self.session_id)
    
  def build_seeds_key(self):
    return 'cassandra-seeds-{}-{}'.format(self.cluster_name, self.datacenter)

  def build_snapshot_key(self):
    return 'cassandra-snapshot-{}-{}'.format(self.datacenter, gethostname())

  def load_or_create_session(self):
    if exists(Cassandra.FILE_SESSION_ID):
      log('found session file')
      with open(Cassandra.FILE_SESSION_ID, 'r') as session_file:
        return session_file.read()

    log('creating new session')
    return self.consul.session.create(self.id, behavior='delete', ttl=120)

  def persist_session(self):
    with open(Cassandra.FILE_SESSION_ID, 'w') as session_file:
      session_file.write(self.session_id)

    log('renewing persisted session: {}'.format(self.session_id))
    self.consul.session.renew(self.session_id)

  def query_snapshot_state(self):
    _, snapshot = self.consul.kv.get(self.build_snapshot_key())

    if snapshot is None:
      return None

    return snapshot['Value']

  def query_seeds(self):
    _, seeds = self.consul.kv.get(self.build_seeds_key())
    if seeds is None:
      return None

    if seeds['Value'] is None:
      return []

    return seeds['Value'].split(',')

  def read_saved_seeds(self, should_retry=True):
    loaded_conf = None
    seed_list = []
    with open('/etc/cassandra/cassandra.yaml', 'r') as conf:
      try:
        loaded_conf = yaml.load(conf)
      except YAMLError as exc:
        log('error occurred while reading cassandra configuration:', exc)
        return []

    if loaded_conf is None:
      if should_retry:
        log('our configuration file was missing!?')
        self.render_config()
        return self.read_saved_seeds(should_retry=False)
      else:
        log('config file missing after retry! raising error')
        raise ValueError('failed to render and load configuration')

    try:
      seed_list = loaded_conf['seed_provider'][0]['parameters'][0]
    except KeyError as e:
      log('error occurred while accessing configuration file seed list:', e)

    return seed_list

  def enough_seeds_exist(self, seeds):
    if seeds is None:
      return False

    parsed_seeds = [s.strip() for s in seeds]
    # ideally there should be two (three max) seeds per DC, but we'll start with just one
    return 0 < len(parsed_seeds)

  def already_registered_as_seed(self, seeds):
    if seeds is None:
      return False

    return gethostbyname(gethostname()) in [s.strip() for s in seeds]

  def register_as_seed(self, seeds):
    if seeds is None:
      seeds = []

    own_ip = gethostbyname(gethostname())

    seeds.append(own_ip)

    return self.consul.kv.put(self.build_seeds_key(), ','.join(seeds))

  def render_config(self):
    check_call([
      'consul-template', '-once', '-template', '/etc/cassandra/cassandra.yaml.ctmpl:/etc/cassandra/cassandra.yaml'])
    log('template rendered to: {}'.format('/etc/cassandra/cassandra.yaml'))

  def record_snapshots(self):
    """
    records a snapshot of all keyspaces tagged with the current UTC datetime
    :return the snapshot tag, as ISO8601 UTC (condensed) datetime
    """
    if self.storage is None:
      return None

    dt = datetime.utcnow().strftime('%Y%m%dT%H%M%S')

    try:
      snapshot = check_output([
        'nodetool', '-u', self.user, '-pw', self.password, 'snapshot', '--tag', dt],
        stderr=STDOUT)
      log('snapshot result: {}'.format(snapshot))
    except CalledProcessError as e:
      log('snapshot failed: {}'.format(e.output))


    return dt

  def ship_snapshots(self, snapshot_tag, keyspaces=None):

    zipped_snapshot = None

    if keyspaces is None:
      keyspaces = self.list_keyspaces()

    if 0 == len(keyspaces):
      raise Exception('no keyspaces to search for snapshots')

    log('shipping snapshots for keyspaces: {}'.format(str(keyspaces)))

    # for ks in keyspaces:
    #   self.home()

  def list_keyspaces(self):
    keyspaces = []

    try:
      keyspace_output = check_output([
        'cqlsh', '-u', self.user, '-pw', self.password, '--no-color', '-e', 'DESCRIBE KEYSPACES'],
        stderr=STDOUT)

      keyspaces = keyspace_output.strip().split()
    except CalledProcessError as e:
      raise Exception('error occurred while listing keyspaces: {}'.format(e.output))

    return keyspaces

  def stop(self):
    stopdaemon = check_output([
      'nodetool', '-u', self.user, '-pw', self.password, 'stopdaemon'])
    log('stopdaemon result: {}'.format(stopdaemon))
