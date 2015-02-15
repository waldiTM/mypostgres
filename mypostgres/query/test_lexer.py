from .lexer import SqlLexer, SqlKeyword, SqlString


class TestSqlLexer:
    def test_keyword(self):
        l = SqlLexer()

        i = l('INSERT')[0]
        assert i == SqlKeyword.INSERT
        i = l('insert')[0]
        assert i == SqlKeyword.INSERT
        i = l('InSeRt')[0]
        assert i == SqlKeyword.INSERT

    def test_string(self):
        l = SqlLexer()

        i = l(r"'test'")[0]
        assert i == "test"
        i = l(r"'te''st'")[0]
        assert i == "te'st"
        i = l(r"'te\'st'")[0]
        assert i == "te'st"

    def test_whitespace(self):
        l = SqlLexer()

        i = l(" ")
        assert i == [None]
        i = l("\t")
        assert i == [None]
        i = l("\n")
        assert i == [None]
        i = l("  ")
        assert i == [None]


def test_SqlString():
    t = SqlString("test")
    assert t.__sql__() == "'test'"
    t = SqlString("te'st")
    assert t.__sql__() == "'te''st'"
