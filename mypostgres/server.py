import psycopg2

from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet
from mysqlproto.server import MysqlServer

from .query import Query


class ServerPsycopg2(MysqlServer):
    def __init__(self, reader, writer, dsn):
        super().__init__(reader, writer)
        self.dsn = dsn
        self.query_rewrite = Query(self)

    def connection_made(self):
        self.conn = psycopg2.connect('')

    def connection_lost(self, exc):
        self.conn.close()

    def query(self, packet):
        query = (yield from packet.read()).decode('ascii')
        print("<=   query:", query)

        ret = self.query_rewrite(query)

        if isinstance(ret, str):
            curs = self.conn.cursor()
            curs.execute(query)

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
            return ERR(self.capability)
