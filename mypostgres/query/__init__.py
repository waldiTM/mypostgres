from .lexer import MysqlLexerTraditional, SqlQuery, SqlKeyword, SqlName, SqlParameter, SqlParenthesis, SqlUnknown


class Query:
    def DELETE(self, query, lex):
        return lex.__sql__()

    def INSERT(self, query, lex):
        return lex.__sql__()

    def SELECT(self, query, lex):
        ret = lex.__class__()
        print(lex)
        for i in lex:
            if isinstance(i, SqlParameter):
                if i == '@@version_comment':
                    i = SqlUnknown('version() as "@@version_comment"')
            ret.append(i)
        print(ret)
        return ret.__sql__()

    def UPDATE(self, query, lex):
        return lex.__sql__()

    def SET(self, query, lex):
        pass

    def SHOW(self, query, lex):
        if len(lex) == 2:
            obj = lex[1]
            if obj == 'databases':
                return """
                    SELECT n.nspname AS database FROM pg_catalog.pg_namespace n
                        WHERE n.nspname !~ '^pg_'
                        ORDER BY 1
                """
            elif obj == 'tables':
                return """
                    SELECT c.relname AS tables
                        FROM pg_catalog.pg_class c
                            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relkind IN ('r', 'v', 'm', 'f')
                            AND n.nspname !~ '^pg_'
                            AND pg_catalog.pg_table_is_visible(c.oid)
                        ORDER by 1
                """
        pass

    def CREATE(self, query, lex):
        ret = lex.__class__()
        print(lex)

        if lex[1] == 'table':
            for i in lex:
                if isinstance(i, SqlParenthesis):
                    d = i.__class__()
                    for w in self.split_list(i, ','):
                        print(w)
                        if isinstance(w[0], SqlKeyword):
                            if w[0] in ('primary', ):
                                if d:
                                    d.append(SqlUnknown(','))
                                d.extend(w)
                        else:
                            col_name = w.pop(0)
                            col_type = w.pop(0)
                            if col_type in ('int', ):
                                col_type = SqlName('integer')
                            elif col_type in ('enum', ):
                                col_type = SqlName('text')

                            if isinstance(w[0], SqlParenthesis):
                                w.pop(0)

                            o = []
                            while w:
                                i = w.pop(0)
                                if i == 'auto_increment':
                                    col_type = SqlName('serial')
                                elif i == 'collate':
                                    w.pop(0)
                                else:
                                    o.append(i)
                            if d:
                                d.append(SqlUnknown(','))
                            d.extend((col_name, col_type))
                            d.extend(o)
                    ret.append(d)
                    break
                else:
                    ret.append(i)
        print(ret)
        return ret.__sql__()

    def DROP(self, query, lex):
        return lex.__sql__()

    def LOCK(self, query, lex):
        pass

    def UNLOCK(self, query, lex):
        pass

    lexer = MysqlLexerTraditional()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        return getattr(self, lex[0].value)(query, lex)

    @staticmethod
    def split_list(l, sep):
        cur = 0
        end = len(l)
        while True:
            try:
                i = l.index(sep, cur)
                yield l[cur:i]
                cur = i + 1
            except ValueError:
                yield l[cur:end]
                break
