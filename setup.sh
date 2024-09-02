#!/bin/bash
# use .env if in production($DEBUG="True", case insensitive) otherwise env/db.env
# ENV_PATH=[[ $DEBUG == "True" ]] && echo ".env" || echo "env/db.env"
ENV_PATH=$([[ $(echo $DEBUG | tr '[:upper:]' '[:lower:]') == "true" ]] && echo "env/db.env" || echo ".env")
ALEMBIC_PATH=$HOME/alembic_venv/bin/alembic

source $ENV_PATH
function setup_mariadb(){
    echo "Initializing MariaDB database..."

    sudo mariadb -u root -p${MYSQL_ROOT_PASSWORD} <<EOF
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';
GRANT ALL PRIVILEGES ON test_${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
EOF

    echo "MariaDB database initialized with database: '${MYSQL_DATABASE}' and user: '${MYSQL_USER}'"
}

function setup_alembic(){
    if [[ ! -d $ALEMBIC_PATH ]]; then
      echo "Alembic not found, create virtual environment and install alembic"
      python3 -m venv $HOME/alembic_venv
      $HOME/alembic_venv/bin/pip install alembic sqlmodel aiomysql python-dotenv
    fi
    sudo mariadb -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} <<EOF
    DROP TABLE IF EXISTS alembic_version;
EOF
    echo "Alembic table dropped"
    echo "Running alembic revision and upgrade..."
    rm -rf migrate/versions/*
    $ALEMBIC_PATH revision --autogenerate -m "Auto generated revision" && $ALEMBIC_PATH upgrade head
}
setup_mariadb && setup_alembic
