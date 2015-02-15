from .lexer import MysqlLexer, SqlKeyword


class Query:
    def SELECT(self, query, lex):
        pass

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
