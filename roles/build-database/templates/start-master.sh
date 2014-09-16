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

	umask=$(umask)
	umask 0077
	echo "topsecret" > /tmp/pwfile
	chown $USER:$USER /tmp/pwfile
	ls -l /tmp/pwfile

	HOME=$DATA \
	setuid postgres \
	$POSTGRES/bin/initdb \
		--pgdata $DATA \
		--pwfile /tmp/pwfile \
		--username postgres \
		--encoding unicode \
		--auth trust \
		--auth-local trust \
		--auth-host md5

	cat >$DATA/pg_hba.conf <<-EOF

		# trust connections from localhost
		local all all trust
		host all all 127.0.0.1/32 trust

		# md5 password from network
		host all all 0.0.0.0/0 md5

		# md5 password for replication
		host replication rep 0.0.0.0/0 md5

	EOF

	cat >$DATA/postgresql.conf <<-EOF

		# connection
		listen_addresses = '*'
		port = 5432
		max_connections = 100

		# replication
		wal_level = 'hot_standby'
		archive_mode = on
		archive_command = 'cd .'
		max_wal_senders = 1
		hot_standby = on

		# misc
		shared_buffers = 128MB
		log_timezone = 'UTC'
		datestyle = 'iso, mdy'
		timezone = 'UTC'
		lc_messages = 'C'
		lc_monetary = 'C'
		lc_numeric = 'C'
		lc_time = 'C'
		default_text_search_config = 'pg_catalog.english'

	EOF

	FIRST_RUN="yes"

fi

echo "-- starting postgres"

setuid postgres \
$POSTGRES/bin/postgres \
	-D $DATA &

if test "$FIRST_RUN"; then

	echo "-- sleeping"

	sleep 2

	echo "-- creating replication user"

	setuid postgres \
	psql \
		-c "

			CREATE USER rep
			REPLICATION LOGIN
			ENCRYPTED PASSWORD 'topsecret';

			ALTER USER postgres
			ENCRYPTED PASSWORD 'topsecret';

		"

fi

echo "-- starting shell"

while true; do
	/bin/bash
	echo "To detach, type C-p C-q"
done
