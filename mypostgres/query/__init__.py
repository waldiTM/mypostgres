from .lexer import MysqlLexerTraditional, SqlKeyword, SqlParameter, SqlUnknown


class Query:
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
        print(lex)
        return lex.__sql__()

    def DROP(self, query, lex):
        return lex.__sql__()

    lexer = MysqlLexerTraditional()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        return getattr(self, lex[0].value)(query, lex)
