from .lexer import MysqlLexerTraditional, SqlKeyword, SqlParameter, SqlUnknown


class Query:
    def SELECT(self, query, lex):
        ret = []
        print(lex)
        for i in lex:
            if isinstance(i, SqlParameter):
                if i == '@@version_comment':
                    i = SqlUnknown('version() as "@@version_comment"')
            ret.append(i)
        print(ret)
        return self.unlex(ret)

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

    lexer = MysqlLexerTraditional()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        return getattr(self, lex[0].value)(query, lex)

    def unlex(self, lex):
        ret = []
        for i in lex:
            ret.append(i.__sql__())
            ret.append(' ')
        return ''.join(ret)
