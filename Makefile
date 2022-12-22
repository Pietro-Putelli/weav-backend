CURRENT_DIRECTORY := $(shell pwd)

TESTSCOPE = apps
TESTFLAGS = --with-timer --timer-top-n 10 --keepdb


start:
	@docker start "database"
	@docker start "nsfw"
	@docker start "redis"

stop:
	@docker stop "database"
	@docker stop "nsfw"
	@docker stop "redis"
