#!/bin/bash

set -e

VERSION=9.3
POSTGRES=/usr/lib/postgresql/$VERSION
USER=postgres
DATA=/data/postgresql

if ! test -d "$DATA"; then

	echo "-- initialising $DATA"

	mkdir -p $DATA

	chown $USER:$USER $DATA
	chmod 0700 $DATA

	sleep 5

	PGUSER=rep \
	PGPASSWORD=topsecret \
	setuid postgres \
	pg_basebackup \
		--write-recovery-conf \
		--pgdata "$DATA" \
		--host "$DATABASE_MASTER_HOSTNAME" \
		--port "$DATABASE_MASTER_PORT"

fi

echo "-- starting postgres"

setuid postgres \
$POSTGRES/bin/postgres \
	-D $DATA &

echo "-- starting shell"

while true; do
	/bin/bash
	echo "To detach, type C-p C-q"
done
