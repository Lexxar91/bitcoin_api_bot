from pony import orm

from database.models import *


db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
orm.sql_debug(True)


