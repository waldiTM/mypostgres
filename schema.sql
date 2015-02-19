CREATE SCHEMA mysql_support;

CREATE OR REPLACE FUNCTION mysql_support.database() RETURNS name
    LANGUAGE sql AS $$
        select current_schema()
    $$;

CREATE OR REPLACE FUNCTION mysql_support.if(iftest boolean, iftrue character, iffalse character) RETURNS character
    LANGUAGE sql AS $$
        select case when iftest then iftrue else iffalse end
    $$;

CREATE OR REPLACE FUNCTION mysql_support.mysql_variable_setup() RETURNS void
    LANGUAGE plpgsql AS $$ 
        begin
            create temporary table mysql_variable (system boolean, key text, value text) on commit preserve rows;
            insert into mysql_variable values (TRUE, 'version_comment', version());
        end;
    $$;

CREATE OR REPLACE FUNCTION mysql_support.mysql_variable_show(system_ boolean, key_ text) RETURNS text
    LANGUAGE plpgsql AS $$
        declare
	    ret text;
        begin
            select value into ret from mysql_variable where system = system_ and key = key_;
	    return ret;
        end;
    $$;


