from .lexer import MysqlLexerTraditional, SqlQuery, SqlKeyword, SqlName, SqlParenthesis, SqlUnknown, SqlVarSystem, SqlVarUser


class Query:
    def DELETE(self, query, lex):
        return lex.__sql__()

    def INSERT(self, query, lex):
        return lex.__sql__()

    def SELECT(self, query, lex):
        ret = self.rewrite_SELECT(lex)
        return ret.__sql__()

    def UPDATE(self, query, lex):
        return lex.__sql__()

    def BEGIN(self, query, lex):
        return lex.__sql__()

    def ROLLBACK(self, query, lex):
        return lex.__sql__()

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

    def ALTER(self, query, lex):
        pass

    def CREATE(self, query, lex):
        found = None
        for i in range(len(lex)):
            if lex[i] in (SqlKeyword.TABLE, SqlKeyword.VIEW):
                leader = lex[1:i-1]
                found = lex[i]
                name = lex[i+1]
                follow = lex[i+2:]
                break

        if not found:
            return

        ret = lex.__class__((lex[0], found, name))

        if found == SqlKeyword.TABLE:
            for i in follow:
                if isinstance(i, SqlParenthesis):
                    ret.append(self.rewrite_CREATE_TABLE_def(i))

        elif found == SqlKeyword.VIEW:
            ret.extend(self.rewrite_SELECT(follow))

        print("rewritten:", ret)
        return ret.__sql__()

    def DROP(self, query, lex):
        return lex.__sql__()

    def LOCK(self, query, lex):
        pass

    def UNLOCK(self, query, lex):
        pass

    def rewrite_SELECT(self, lex):
        ret = lex.__class__()
        self.rewrite_SELECT_output(lex, ret)
        while lex:
            i = lex.pop(0)
            ret.append(i)
            if i in (SqlKeyword.WHERE, SqlKeyword.HAVING):
                d = SqlParenthesis()
                ret.append(d)
                ret.append(SqlUnknown(b'::bool'))
                if isinstance(lex[0], SqlKeyword):
                    break
                d.append(lex.pop(0))
        return ret

    def rewrite_SELECT_output(self, lex, out):
        while lex:
            i = lex.pop(0)
            if i == SqlKeyword.FROM:
                out.append(i)
                break

            elif isinstance(i, SqlVarSystem):
                j = SqlUnknown(b'mysql_variable_show(TRUE, \'' + i + b'\') as "' + i.context + b'"')
                out.append(j)

            elif isinstance(i, SqlVarUser):
                # XXX: Can user variables be modified here?
                j = SqlUnknown(b'mysql_variable_show(FALSE, \'' + i + b'\') as "@' + i + b'"')
                out.append(j)

            elif isinstance(i, SqlParenthesis):
                l = i.__class__()
                self.rewrite_SELECT_output(i, l)
                out.append(l)

            elif i == SqlKeyword.CAST:
                out.append(i)
                j = lex.pop(0)
                if isinstance(j, SqlParenthesis):
                    l = j.__class__()
                    try:
                        k = j.index(b'charset')
                        j = j[:k]
                    except ValueError:
                        pass
                    self.rewrite_SELECT_output(j, l)
                    out.append(l)

            elif i == SqlKeyword.COALESCE:
                out.append(i)
                j = lex.pop(0)
                if isinstance(j, SqlParenthesis):
                    l = j.__class__()
                    out.append(l)
                    for w in self.split_list(j, b','):
                        if l:
                            l.append(SqlUnknown(b','))
                        self.rewrite_SELECT_output(w, l)
                        l.append(SqlUnknown(b'::text'))

            elif i == b'convert':
                j = lex.pop(0)
                if isinstance(j, SqlParenthesis):
                    try:
                        k = j.index(b'using')
                        j = j[:k]
                    except ValueError:
                        pass
                    self.rewrite_SELECT_output(j, out)

            else:
                out.append(i)

    def rewrite_CREATE_TABLE_def(self, lex):
        d = lex.__class__()
        for w in self.split_list(lex, b','):
            if isinstance(w[0], SqlKeyword):
                if w[0] in (b'primary', ):
                    if d:
                        d.append(SqlUnknown(b','))
                    d.extend(w)
            else:
                col_name = w.pop(0)
                col_type = w.pop(0)

                if col_type in (b'tinyint', ):
                    col_type = SqlName(b'smallint')
                elif col_type in (b'longtext', ):
                    col_type = SqlName(b'text')
                elif col_type in (b'tinyblob', b'longblob', b'blob'):
                    col_type = SqlName(b'bytea')
                elif col_type in (b'datetime', ):
                    col_type = SqlName(b'timestamp')
                elif col_type in (b'enum', ):
                    col_type = SqlName(b'text')

                if w and isinstance(w[0], SqlParenthesis):
                    w.pop(0)

                o = []
                while w:
                    i = w.pop(0)
                    if i == b'auto_increment':
                        col_type = SqlName(b'serial')
                    elif i == SqlKeyword.COLLATE:
                        w.pop(0)
                    elif i == b'unsigned':
                        pass
                    else:
                        o.append(i)
                if d:
                    d.append(SqlUnknown(b','))
                d.extend((col_name, col_type))
                d.extend(o)
        return d

    lexer = MysqlLexerTraditional()

    def __init__(self, server):
        self.server = server

    def __call__(self, query):
        lex = self.lexer(query)
        if lex:
            print(lex)
            return getattr(self, lex[0].value)(query, lex)

    @staticmethod
    def split_list(l, sep):
        cur = 0
        end = len(l)
        while True:
            try:
                i = l.index(sep, cur)
                yield l[cur:i]
                cur = i + 1
            except ValueError:
                yield l[cur:end]
                break
