CREATE SCHEMA mysql_support;

CREATE OR REPLACE FUNCTION mysql_support.database() RETURNS name
    LANGUAGE sql AS $$
        select current_schema()
    $$;

CREATE OR REPLACE FUNCTION mysql_support.if(iftest boolean, iftrue character, iffalse character) RETURNS character
    LANGUAGE sql AS $$
        select case when iftest then iftrue else iffalse end
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


