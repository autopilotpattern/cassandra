#!/usr/bin/env python
from sys import stderr
from os import environ, listdir
from subprocess import check_output, Popen, PIPE, CalledProcessError

class termcolor:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  END = '\033[0m'

def die(err):
  if isinstance(err, CalledProcessError):
    msg = err.output
  else
    msg = err

  print >> stderr, termcolor.FAIL + err + termcolor.END
  exit(1)

if 'CASSANDRA_USER' not in environ or 'CASSANDRA_PASSWORD' not in environ:
  print >> stderr, '{} environment is missing CASSANDRA_USER or CASSANDRA_PASSWORD! {}'.format(termcolor.FAIL, termcolor.END)
  exit(1)

CASSANDRA_USER = environ["CASSANDRA_USER"]
CASSANDRA_PASSWORD = environ["CASSANDRA_PASSWORD"]

status = "UNKNOWN"
try:
  status = check_output([
    "nodetool", "-u", CASSANDRA_USER, "-pw", CASSANDRA_PASSWORD, "status"])
except CalledProcessError as e:
    die(e)

print "node status: {} {} {}".format(termcolor.OKGREEN, status, termcolor.END)

try:
  check_call([
    "consul-template", "-once", "-template", "/etc/cassandra/cassandra.yaml.ctmpl:/etc/cassandra/cassandra.yaml"])
except CalledProcessError as e:
    die(e)

print "template ", template

# calling stopdaemon brings down cassandra.
# it should be brought back up by containerpilot and read the new cassandra.yml
stopdaemon = check_output([
  "nodetool", "-u", "cassandra", "-pw", "cassandra", "stopdaemon"])

print "stopdaemon result: ", stopdaemon

# TODO: dont stopdaemon unless there are enough other nodes available
# if [ $((`nodetool -u cassandra -pw cassandra status | grep -v $HOSTNAME | grep UN | wc -l`)) -gt 1 ]; then
#   nodetool -u cassandra -pw cassandra stopdaemon
# fi

