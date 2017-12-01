build:
	docker-compose \
		-p autopilotpattern \
		-f examples/compose/docker-compose.yml \
		build cassandra

up:
	docker-compose \
		-p autopilotpattern \
		-f examples/compose/docker-compose.yml \
		up

down:
	docker-compose \
		-p autopilotpattern \
		-f examples/compose/docker-compose.yml \
		down --remove-orphans -v

ps:
	docker-compose \
		-p autopilotpattern \
		-f examples/compose/docker-compose.yml \
		ps

