CREATE SCHEMA mysql_support;

/* MySQL function */
CREATE OR REPLACE FUNCTION mysql_support.database() RETURNS name
    LANGUAGE sql AS $$
        select current_schema()
    $$;

CREATE OR REPLACE FUNCTION mysql_support.if(boolean, anyelement, anyelement) RETURNS anyelement
    LANGUAGE sql AS $$
        select case when $1 then $2 else $3 end
    $$;

CREATE OR REPLACE FUNCTION mysql_support.last_insert_id() RETURNS bigint
    LANGUAGE sql AS $$
        select pg_catalog.lastval()
    $$;

CREATE OR REPLACE FUNCTION mysql_support.last_insert_id(bigint) RETURNS bigint
    LANGUAGE plpgsql AS $$
        declare
            ret bigint;
        begin
            perform pg_catalog.setval('mysql_sequence', $1, false);
            select pg_catalog.nextval('mysql_sequence') into ret;
	    return ret;
	end;
    $$;

/* Helper functions */
CREATE OR REPLACE FUNCTION mysql_support.mysql_variable_show(boolean, text) RETURNS text
    LANGUAGE plpgsql AS $$
        declare
            ret text;
        begin
            select value into ret from mysql_variable where system = $1 and key = $2;
            return ret;
        end;
    $$;

CREATE OR REPLACE FUNCTION mysql_support.mysql_variable_set(boolean, text, text) RETURNS void
    LANGUAGE plpgsql AS $$
        begin
            update mysql_variable set value = $3 where system = $1 and key = $2;
            if found then
                return;
            end if;
            insert into mysql_variable (system, key, value) values ($1, $2, $2);
        end;
    $$;
