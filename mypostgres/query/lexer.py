from enum import Enum
import re


class SqlKeyword(Enum):
    delete = "DELETE"
    insert = "INSERT"
    select = "SELECT"
    replace = "REPLACE"
    update = "UPDATE"

    begin = "BEGIN"
    commit = "COMMIT"
    rollback = "ROLLBACK"

    set = "SET"
    show = "SHOW"

    alter = "ALTER"
    create = "CREATE"
    drop = "DROP"
    rename = "RENANE"
    truncate = "TRUNCATE"

    def __sql__(self):
        return self.name


class SqlName(str):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        # XXX
        return self


class SqlParameter(str):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        raise RuntimeError


class SqlString(str):
    def __new__(cls, t):
        return super().__new__(cls, t)

    def __repr__(self):
        return "<{}: '{}'>".format(self.__class__.__name__, self)

    def __sql__(self):
        return "'" + self.replace("'", "''") + "'"


class SqlUnknown(str):
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
            self.rules.append('(?P<{}>{})'.format(f.__name__, rule))
            return f
        return decorator

    def compile(self):
        return re.compile('|'.join(self.rules), re.I | re.X)


class MysqlLexer:
    syntax = Syntax()

    @syntax.add(r' (?P<parameter>@@)? [a-z_]+ ')
    def bare_id(self, bare_id, parameter=None):
        if parameter:
            return SqlParameter(bare_id)
        bare_id = bare_id.lower()
        return getattr(SqlKeyword, bare_id, SqlName(bare_id))

    @syntax.add(r'''[-+*/=()]''')
    def operator(self, operator):
        return SqlUnknown(operator)

    @syntax.add(r''' (?: '.*?(?<!\\)' )+ ''')
    def string(self, string):
        return SqlString(string.strip("'").replace("''", "'").replace(r"\'", "'"))

    @syntax.add(r''' (?: ".*?(?<!\\)" )+ ''')
    def string_id(self, string_id):
        return SqlName(string_id)

    @syntax.add(r''' (?: `.*?(?<!\\)` )+ ''')
    def string_back(self, string_back):
        raise NotImplementedError

    @syntax.add('\s+')
    def whitespace(self, whitespace):
        return None

    @syntax.add('.+?')
    def rest(self, rest):
        return SqlUnknown(rest)

    _re = syntax.compile()

    def __call__(self, text):
        ret = []
        for match in self._re.finditer(text):
            data = dict(((str(k), v) for k, v in match.groupdict().items() if v is not None))
            ret.append(getattr(self, match.lastgroup)(**data))
        return ret


class MysqlLexerTraditional(MysqlLexer):
    def string_id(self, string_id):
        return SqlString(string_id.strip('"'))

    def string_back(self, string_back):
        return SqlName(string_back.replace('`', '"'))
