CREATE DATABASE {{ db.NAME }}
DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
GRANT ALL on {{ db.NAME }}.*
to '{{ db.USER }}'@'{{ db.HOST|default:'localhost' }}'
identified by '{{ db.PASSWORD }}' WITH GRANT OPTION;
