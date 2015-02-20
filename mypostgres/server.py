import logging
import psycopg2

from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet
from mysqlproto.server import MysqlServer

from .query import Query

logger = logging.getLogger(__name__)


class ServerPsycopg2(MysqlServer):
    def __init__(self, reader, writer, dsn):
        super().__init__(reader, writer)
        self.dsn = dsn
        self.query_rewrite = Query(self)

    def connection_made(self, user, schema):
        # XXX: user
        self.conn = psycopg2.connect('')
        self.conn.autocommit = True
        self.schema_change(schema)

        with self.conn.cursor() as curs:
            curs.execute(r'''create temporary table mysql_variable (system boolean, key text, value text) on commit preserve rows''')
            curs.execute(r'''insert into mysql_variable values (TRUE, 'character_set_connection', 'utf8')''')
            curs.execute(r'''insert into mysql_variable values (TRUE, 'version_comment', version())''')
        self.conn.commit()
        yield

    def connection_lost(self, exc):
        self.conn.close()
        yield

    def query(self, packet):
        query = (yield from packet.read())

        try:
            query_new = self.query_rewrite(query)
        except:
            logger.exception('Failed to rewrite: %s', query.decode('ascii', 'replace'))
            raise

        if isinstance(query_new, bytes):
            curs = self.conn.cursor()
            try:
                curs.execute(query_new)
            except:
                logger.exception('Failed to execute: %s', query_new.decode('ascii', 'replace'))
                logger.info('Was: %s', query.decode('ascii', 'replace'))
                raise

            if curs.description:
                cd = ColumnDefinitionList()
                for d in curs.description:
                    cd.columns.append(ColumnDefinition(d.name))
                cd.write(self.writer)
                EOF(self.capability, self.status).write(self.writer)

                while True:
                    i = curs.fetchone()
                    if not i:
                        break
                    ResultSet(i).write(self.writer)
                return EOF(self.capability, self.status)

            else:
                return OK(self.capability, self.status, info=curs.statusmessage)

        else:
            return OK(self.capability, self.status)

    def schema_change(self, schema):
        curs = self.conn.cursor()
        curs.execute('set search_path to "{}",mysql_support'.format(schema))
        self.schema = schema
