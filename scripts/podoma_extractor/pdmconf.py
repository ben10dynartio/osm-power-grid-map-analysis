import os

import psycopg2
from psycopg2.extras import register_hstore

dbname=os.getenv("PODOMA_DBNAME", "podoma")
user=os.getenv("PODOMA_DBUSER", "podoma")
password=os.getenv("PODOMA_DBPASS", "podomapass")
host=os.getenv("PODOMA_DBHOST", "localhost")
port=os.getenv("PODOMA_DBPORT", "5432")

OSM_POWER_TAGS = ["ref", "name", "type", "route", "power", "voltage", "substation", "line", "circuits", "cables", "wires", "operator", "operator:wikidata", "location", "note", "wikidata", "topology", "frequency", "line_management"]
OUTPUT_FOLDER_NAME = "shapes"

def connectpdm(dbname=dbname, user=user, password=password, host=host, port=port):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    register_hstore(conn)

    return conn