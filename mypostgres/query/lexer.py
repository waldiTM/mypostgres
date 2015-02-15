from enum import Enum
import re


class SqlKeyword(Enum):
    DELETE = "delete"
    INSERT = "insert"
    SELECT = "select"
    REPLACE = "replace"
    UPDATE = "update"

    BEGIN = "begin"
    COMMIT = "commit"
    ROLLBACK = "rollback"

    SET = "set"
    SHOW = "show"

    ALTER = "alter"
    CREATE = "create"
    DROP = "drop"
    RENAME = "rename"
    TRUNCATE = "truncate"

    def __sql__(self):
        return self.name


class SqlString(str):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __sql__(self):
        return "'" + self.replace("'", "''") + "'"


class Syntax:
    __slots__ = 'rules'

    def __init__(self):
        self.rules = []

    def add(self, rule):
        def decorator(f):
            self.rules.append('(?P<{}>{})'.format(f.__name__, rule))
            return f
        return decorator

    def compile(self):
        return re.compile('|'.join(self.rules), re.I | re.X)


class MysqlLexer:
    syntax = Syntax()

    @syntax.add('|'.join(SqlKeyword.__members__))
    def keyword(self, keyword):
        return SqlKeyword[keyword.upper()]

    @syntax.add(r'[a-z]+')
    def id(self, id):
        return id.lower()

    @syntax.add(r'''[-+*/=()]''')
    def operator(self, operator):
        return operator

    @syntax.add(r''' (?: '.*?(?<!\\)' )+ ''')
    def string(self, string):
        return SqlString(string.strip("'").replace("''", "'").replace(r"\'", "'"))

    @syntax.add(r''' (?: ".*?(?<!\\)" )+ ''')
    def string_id(self, text):
        raise NotImplementedError

    @syntax.add(r''' (?: `.*?(?<!\\)` )+ ''')
    def string_back(self, text):
        raise NotImplementedError

    @syntax.add('\s+')
    def whitespace(self, whitespace):
        return None

    @syntax.add('.')
    def rest(self, rest):
        raise RuntimeError

    _re = syntax.compile()

    def __call__(self, text):
        ret = []
        for match in self._re.finditer(text):
            data = dict(((str(k), v) for k, v in match.groupdict().items() if v is not None))
            ret.append(getattr(self, match.lastgroup)(**data))
        return ret


class MysqlLexerTraditional(MysqlLexer):
    string_id = MysqlLexer.string
    string_back = MysqlLexer.string_id
