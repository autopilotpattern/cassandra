from __future__ import print_function
from os import environ
from os.path import exists
from sys import stderr
from time import sleep
from urlparse import urlparse
from consul import Consul, ConsulException
from containerpilot_handler.storage import Local, Manta

class termcolor:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  END = '\033[0m'

def log(s):
  print('HANDLER: {}{}{}'.format(termcolor.OKBLUE, s, termcolor.END))

def die(err):
  if isinstance(err, Exception):
    msg = err.output
  else:
    msg = err

  print(termcolor.FAIL + err + termcolor.END, file=stderr)
  exit(1)

def resolve_home():
  if 'CASSANDRA_HOME' in environ:
    return environ['CASSANDRA_HOME']

  return '/var/lib/cassandra'

def resolve_cluster_name():
  if 'CASSANDRA_CLUSTER_NAME' in environ:
    return environ['CASSANDRA_CLUSTER_NAME']

  return 'test'

def resolve_credentials():
  if 'CASSANDRA_USER' not in environ or 'CASSANDRA_PASSWORD' not in environ:
    die('environment is missing CASSANDRA_USER or CASSANDRA_PASSWORD!')
  
  return environ["CASSANDRA_USER"], environ["CASSANDRA_PASSWORD"]

def resolve_datacenter(c):
  if 'CASSANDRA_DC' in environ:
    return environ['CASSANDRA_DC']

  # TODO: figure out what priority this mdata-get call should have relative to Consul
  # if exists('/native/usr/sbin/mdata-get') and consul is None:
  #   return check_output('/native/usr/sbin/mdata-get sdc:datacenter_name')

  if not isinstance(c, Consul):
    raise ValueError('unexpected type for consul instance when resolving datacenter: {}'.format(type(c)))

  consulAgentInfo = c.agent.self()

  if 'Config' in consulAgentInfo and 'Datacenter' in consulAgentInfo['Config']:
    return consulAgentInfo['Config']['Datacenter']
  else:
    return None

def resolve_storage():
  if 'SNAPSHOT_TARGET' not in environ:
    return None

  uri = urlparse(environ['SNAPSHOT_TARGET'])
  if 'manta' in uri.scheme:
    return Manta()
  
  if environ['SNAPSHOT_TARGET'].startswith('local'):
    return Local()
  
  return None

def await_leader(consul, max_duration=10, attempts=6):
  known_leader = ''

  while known_leader == '' and 0 < attempts:

    try:
      known_leader = consul.status.leader()
    except ConsulException as e:
      log('no leader elected yet', file=stderr)

    sleep(max_duration / attempts)
    attempts -= 1

  if consul.status.leader() == '':
    raise Exception('no leader elected in time')
