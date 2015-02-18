from .lexer import MysqlLexer, SqlKeyword, SqlString


class TestMysqlLexer:
    def test_keyword(self):
        l = MysqlLexer()

        i = l(b'INSERT')[0]
        assert i == SqlKeyword.INSERT
        i = l(b'insert')[0]
        assert i == SqlKeyword.INSERT
        i = l(b'InSeRt')[0]
        assert i == SqlKeyword.INSERT

    def test_string(self):
        l = MysqlLexer()

        i = l(br"'test'")[0]
        assert i == "test"
        i = l(br"'te''st'")[0]
        assert i == "te'st"
        i = l(br"'te\'st'")[0]
        assert i == "te'st"

    def test_whitespace(self):
        l = MysqlLexer()

        i = l(b" ")
        assert i == []
        i = l(b"\t")
        assert i == []
        i = l(b"\n")
        assert i == []
        i = l(b"  ")
        assert i == []


def test_SqlString():
    t = SqlString("test")
    assert t.__sql__() == "'test'"
    t = SqlString("te'st")
    assert t.__sql__() == "'te''st'"
