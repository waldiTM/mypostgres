from .lexer import MysqlLexer, SqlKeyword, SqlParameter


class Query:
    def SELECT(self, query, lex):
        ret = []
        print(lex)
        for i in lex:
            if isinstance(i, SqlParameter):
                if i == '@@version_comment':
                    i = 'version() as "@@version_comment"'
            ret.append(i)
        print(ret)
        return self.unlex(ret)

    def SET(self, query, lex):
        pass

    def SHOW(self, query, lex):
        pass

    lexer = MysqlLexer()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        return getattr(self, lex[0].name)(query, lex)

    def unlex(self, lex):
        ret = []
        for i in lex:
            if isinstance(i, str):
                ret.append(i)
            elif i is None:
                ret.append(' ')
            else:
                ret.append(i.__sql__())
        return ''.join(ret)
