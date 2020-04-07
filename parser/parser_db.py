import psycopg2
from typing import List, Tuple
from datetime import datetime

class PostgresDatabase():
    sql_create_table = """CREATE TABLE  stowages (
                           product_id text NOT NULL,
                           date_updated timestamp NOT NULL,
                           stuff_type text NOT NULL,
                           location text NOT NULL,
                           location_types text NOT NULL,
                           weight decimal NOT NULL,
                           weight_type text NOT NULL,
                           price_rub integer NOT NULL,
                           price_btc decimal NOT NULL
                       );
                       ALTER TABLE stowages ADD CONSTRAINT  unique_stowage UNIQUE (location,weight,product_id);
                       """

    def __init__(self,connection_string : str):
        self.conn = psycopg2.connect(connection_string)
        self.conn.autocommit = True
        self.conn.set_client_encoding('UTF8')
        self.cur = self.conn.cursor()
        self.cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('stowages',))
        if not self.cur.fetchone()[0]:
         self.cur.execute(self.sql_create_table)

    def add_or_update_stowage(self, product_id : str, stuff_type : str, location: str, location_types : str, weight : float, weight_type : str, price_rub : int, price_btc : float):
        self.cur.execute(
            """INSERT INTO stowages(product_id, date_updated, stuff_type, location, location_types, weight, weight_type, price_rub, price_btc)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT ON CONSTRAINT unique_stowage
                DO UPDATE SET date_updated = %s, location_types = %s, price_rub = %s, price_btc = %s;
                """,
            (product_id, datetime.now(), stuff_type, location, location_types, weight, weight_type, price_rub, price_btc,
             datetime.now(),location_types,price_rub,price_btc
             ))

    def get_all_stowages_type(self,stuff_type : str, limit :int = 100, days : int = 1 ) ->List[Tuple]:
            self.cur.execute("SELECT * FROM stowages WHERE stuff_type = %s AND date_updated >= now() - interval '%s days'  LIMIT %s",(stuff_type,days,limit,))
            return self.cur.fetchall()

    def get_all_stowages(self,limit : int = 100 ) ->List[Tuple]:
            self.cur.execute("SELECT * FROM stowages LIMIT %s",(limit,))
            return self.cur.fetchall()

    def get_unique_stuff(self,limit : int = 100 ) ->List[Tuple]:
            self.cur.execute("SELECT  DISTINCT ON (stuff_type) stuff_type FROM stowages LIMIT %s",(limit,))
            return self.cur.fetchall()

    def delete_older_then(self,days : int = 1) -> None:
            self.cur.execute("DELETE from stowages WHERE date_updated < now() - interval '%s days' ",(days,))
            self.cur.execute("VACUUM ANALYSE stowages")