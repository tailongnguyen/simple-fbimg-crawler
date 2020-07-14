# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlite3 import Error

import sqlite3
import sys


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
        sys.exit()
        
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

class FbimgPipeline(object):

    def __init__(self, database_uri, table_name):
        self.database_uri = database_uri
        self.table_name = table_name
    
    @classmethod
    def from_crawler(cls, crawler):
        print("=" * 30)
        print(crawler.settings.get("SQLITE_URI"))
        print(crawler.settings.get("SQLITE_TABLE"))
        print("=" * 30)
        return cls(
            database_uri=crawler.settings.get("SQLITE_URI"),
            table_name=crawler.settings.get("SQLITE_TABLE")
        )
    
    def open_spider(self, spider):
        self.conn = create_connection(self.database_uri)
        if self.conn is not None:
            sql_create_table = """ CREATE TABLE IF NOT EXISTS {} (
                                                id integer PRIMARY KEY,
                                                uid text NOT NULL,
                                                url text NOT NULL,
                                                width integer,
                                                height integer,
                                                alt text
                                            ); """.format(self.table_name)
            create_table(self.conn, sql_create_table)
        else:
            print("Error! Cannot connect to database!")
            sys.exit()
    
    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        c = self.conn.cursor()
        sql_insert_cmd = """ INSERT INTO {}(uid, url, width, height, alt) VALUES(?, ?, ?, ?, ?)""".format(self.table_name)
        data = (item["uid"], item["url"], item["width"], item["height"], item["alt"])
        c.execute(sql_insert_cmd, data)
        self.conn.commit()

        return item
