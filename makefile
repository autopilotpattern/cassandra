DC := docker-compose -p autopilotpattern -f examples/compose/local-compose.yml

.PHONY: *

build:
	$(DC) build cassandra

up:
	$(DC) up

restart-cassandra:
	$(DC) stop cassandra && $(DC) rm -vf cassandra && $(DC) build cassandra && $(DC) up cassandra

consul:
	$(DC) up -d consul

down:
	$(DC) down --remove-orphans -v

ps:
	$(DC) ps

cqlsh:
	$(DC) exec cassandra cqlsh

pyrepl:
	$(DC) exec cassandra env PYTHONSTARTUP=/.pythonrc python

bash:
	$(DC) exec cassandra bash
