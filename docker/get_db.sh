#!/bin/bash

create_new_db() {

    # Get the list of existing secrets to see if new ones need to be created/updated
    EXISTING_SECRET_LIST="$(docker secret ls)"

    # Persistent data volumes can be created repeatedly with no ill effects, so ensure at the outset
    # that the volume for the Postgres data exists.
    docker volume create danceschool_postgres
    docker run -d --name danceschool_postgres_temp -v danceschool_postgres:/var/lib/postgresql/data postgres:10.6
    sleep 3;

    POSTGRES_USER_EXISTS=$(grep -c "postgres_user" <<< $EXISTING_SECRET_LIST)
    POSTGRES_PASSWORD_EXISTS=$(grep -c "postgres_password" <<< $EXISTING_SECRET_LIST)
    POSTGRES_URL_EXISTS=$(grep -c "postgres_url" <<< $EXISTING_SECRET_LIST)
    DB_EXISTS=$(docker exec danceschool_postgres_temp psql -U postgres -c "\list"| grep -c "danceschool_postgres")


    if [ $POSTGRES_USER_EXISTS -ge 1 ] ; then
        docker secret rm postgres_user
    fi
    if [ $POSTGRES_USER_EXISTS -ge 1 ] ; then
        docker secret rm postgres_password
    fi
    if [ $POSTGRES_URL_EXISTS -ge 1 ] ; then
        docker secret rm postgres_url
    fi
    if [ $DB_EXISTS -ge 1 ] ; then
        docker exec danceschool_postgres_temp psql -U postgres -c "DROP DATABASE danceschool_postgres"
    fi

    POSTGRES_USER=$(< /dev/urandom tr -dc a-z | head -c${1:-32})
    echo "${POSTGRES_USER}" | docker secret create postgres_user -

    POSTGRES_PASSWORD==$(< /dev/urandom tr -dc A-Za-z0-9 | head -c${1:-32})
    echo "${POSTGRES_PASSWORD}" | docker secret create postgres_password -

    echo "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/danceschool_postgres" | docker secret create postgres_url -

    # Create the Postgres user based on the new credentials
    docker exec danceschool_postgres_temp psql -U postgres -c "CREATE USER ${POSTGRES_USER} PASSWORD '${POSTGRES_PASSWORD}'"

    docker exec danceschool_postgres_temp psql -U postgres -c "CREATE DATABASE danceschool_postgres OWNER ${POSTGRES_USER}"

    docker stop danceschool_postgres_temp
    docker rm danceschool_postgres_temp
    
}

docker stack rm school
sleep 3

create_new_db
sleep 3

docker stack deploy -c docker-compose-shellonly.yml danceschool_shellonly
sleep 5

REMOTE_WEB_CONTAINER=$(ssh root@hotboogie.com.ua docker ps | grep gunicorn | awk '{ print $1;}')
LOCAL_WEB_CONTAINER=$(docker ps | grep "danceschool_shellonly_web\.1" | awk '{ print $1;}')
LOCAL_DB_CONTAINER=$(docker ps | grep postgres | awk '{ print $1;}')

ssh root@hotboogie.com.ua docker exec $REMOTE_WEB_CONTAINER python3 manage.py dumpdata > ../custom/db_full.json
ssh root@hotboogie.com.ua "docker exec -iw /data/web/school ${REMOTE_WEB_CONTAINER} tar -c media" | docker exec -iw /data/web/school $LOCAL_WEB_CONTAINER tar -xv

docker exec $LOCAL_WEB_CONTAINER python3 manage.py migrate

docker exec -it $LOCAL_DB_CONTAINER psql -U postgres -d danceschool_postgres -c "TRUNCATE auth_group_permissions CASCADE;"
docker exec -it $LOCAL_DB_CONTAINER psql -U postgres -d danceschool_postgres -c "TRUNCATE auth_permission CASCADE;"
docker exec -it $LOCAL_DB_CONTAINER psql -U postgres -d danceschool_postgres -c "TRUNCATE django_admin_log CASCADE;"
docker exec -it $LOCAL_DB_CONTAINER psql -U postgres -d danceschool_postgres -c "TRUNCATE django_content_type CASCADE;"

docker exec $LOCAL_WEB_CONTAINER python3 manage.py loaddata custom/db_full.json

docker stack rm danceschool_shellonly
sleep 3
docker stack deploy -c ../docker-compose.yml school
