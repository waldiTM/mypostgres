import codecs
from enum import Enum
import re


class SqlQuery(list):
    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, list.__repr__(self))

    def __sql__(self):
        return b' '.join((i.__sql__() for i in self))



class SqlKeyword(Enum):
    ALTER = "ALTER"
    BEGIN = "BEGIN"
    COMMIT = "COMMIT"
    CREATE = "CREATE"
    DELETE = "DELETE"
    DROP = "DROP"
    EXPLAIN = "EXPLAIN"
    INSERT = "INSERT"
    KEY = "KEY"
    LOCK = "LOCK"
    NOT = "NOT"
    NULL = "NULL"
    PRIMARY = "PRIMARY"
    RENAME = "RENANE"
    REPLACE = "REPLACE"
    ROLLBACK = "ROLLBACK"
    SELECT = "SELECT"
    SET = "SET"
    SHOW = "SHOW"
    TRUNCATE = "TRUNCATE"
    UNLOCK = "UNLOCK"
    UPDATE = "UPDATE"

    def __sql__(self):
        return self.name.encode('ascii')


class SqlName(bytes):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        # XXX
        return self


class SqlParameter(bytes):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        raise RuntimeError


class SqlParenthesis(SqlQuery):
    def __sql__(self):
        return b'(' + super().__sql__() + b')'


class SqlString(str):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        return b"'" + self.encode('utf-8').replace(b"'", b"''") + b"'"


class SqlStringUnknown(bytes):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        return br"E'\\x" + codecs.encode(self, 'hex') + b"'"


class SqlUnknown(bytes):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        return self


class Syntax:
    __slots__ = 'rules'

    def __init__(self):
        self.rules = []

    def add(self, rule):
        def decorator(f):
            self.rules.append('(?P<{}>{})'.format(f.__name__, rule).encode('ascii'))
            return f
        return decorator

    def compile(self):
        return re.compile(b'|'.join(self.rules), re.I | re.X)


class MysqlLexer:
    syntax = Syntax()

    @syntax.add(r' /\*\!\d{5} ')
    def comment_open_mysqlversion(self, stack, comment_open_mysqlversion):
        stack.append(stack[-1])

    @syntax.add(r' /\* ')
    def comment_open(self, stack, comment_open):
        stack.append([])

    @syntax.add(r' \*/ ')
    def comment_close(self, stack, comment_close):
        stack.pop()

    @syntax.add(r' \( ')
    def parenthesis_open(self, stack, parenthesis_open):
        p = SqlParenthesis()
        stack[-1].append(p)
        stack.append(p)

    @syntax.add(r' \) ')
    def parenthesis_close(self, stack, parenthesis_close):
        stack.pop()

    @syntax.add(r' (?P<parameter>@@)? [a-z0-9_.]+ ')
    def bare_id(self, stack, bare_id, parameter=None):
        if parameter:
            r = SqlParameter(bare_id)
        else:
            r = getattr(SqlKeyword, bare_id.upper().decode('ascii'), None)
        if not r:
            r = SqlName(bare_id.lower())
        stack[-1].append(r)

    @syntax.add(r'''[-+*/=]''')
    def operator(self, stack, operator):
        stack[-1].append(SqlUnknown(operator))

    @syntax.add(r''' (?: '.*?(?<!\\)' )+ ''')
    def string(self, stack, string):
        r = string.strip(b"'").replace(b"''", b"'").replace(br"\'", b"'")
        try:
            r = SqlString(r.decode('utf-8'))
        except UnicodeDecodeError:
            r = SqlStringUnknown(r)
        stack[-1].append(r)

    @syntax.add(r''' (?: ".*?(?<!\\)" )+ ''')
    def string_id(self, stack, string_id):
        stack[-1].append(SqlName(string_id))

    @syntax.add(r''' (?: `.*?(?<!\\)` )+ ''')
    def string_back(self, stack, string_back):
        raise NotImplementedError

    @syntax.add('\S+?')
    def rest(self, stack, rest):
        stack[-1].append(SqlUnknown(rest))

    _re = syntax.compile()

    def __call__(self, text):
        stack = [SqlQuery()]
        for match in self._re.finditer(text):
            data = dict(((str(k), v) for k, v in match.groupdict().items() if v is not None))
            getattr(self, str(match.lastgroup))(stack, **data)
        return stack[0]


class MysqlLexerTraditional(MysqlLexer):
    def string_id(self, stack, string_id):
        stack[-1].append(SqlString(string_id.decode('utf-8').strip('"')))

    def string_back(self, stack, string_back):
        stack[-1].append(SqlName(string_back.replace(b'`', b'"')))
