from .lexer import SqlLexer, SqlKeyword


class Query:
    def SET(self, query, lex):
        pass

    def SHOW(self, query, lex):
        pass

    lexer = SqlLexer()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        return getattr(self, lex[0].name)(query, lex)
