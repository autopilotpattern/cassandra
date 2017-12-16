DC := docker-compose

CONSUL_ADDR := $(shell $(DC) ps consul | egrep -o '0.0.0.0:\d+' | head -1)
CONSUL_URL := $(shell echo "http://$(CONSUL_ADDR)")

.PHONY: *

build:
	$(DC) build cassandra

up:
	$(DC) up

restart-cassandra:
	$(DC) stop cassandra
	$(DC) rm -vf cassandra
	$(DC) build cassandra
	$(DC) up -d --scale=cassandra=1 --scale=consul=3 cassandra consul
	$(DC) logs -f cassandra

consul:
	open $(CONSUL_URL)

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
