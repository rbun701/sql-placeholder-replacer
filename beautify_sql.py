import streamlit as st
import sqlparse

def beautify_sql(sql: str) -> str:
    return sqlparse.format(
        sql,
        keyword_case='upper',
        identifier_case=None,
        strip_comments=False,
        reindent=True,
        indent_width=4,
        use_space_around_operators=True
    )

st.title("SQL Beautifier")

sql_input = st.text_area("Paste your SQL here:")
if st.button("Beautify"):
    if sql_input.strip():
        beautified = beautify_sql(sql_input)
        st.code(beautified, language='sql')
    else:
        st.warning("Please enter some SQL.")
