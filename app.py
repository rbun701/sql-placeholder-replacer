import streamlit as st
import re

st.title("🔄 Pega SQL Placeholder Replacer")
st.markdown("Paste your SQL and SQL Insert values below. This tool replaces `?` with each value in order.")

sql_query = st.text_area("Paste SQL Query with `?` placeholders:", height=300)
sql_inserts_raw = st.text_area("Paste SQL Inserts (e.g. `<Val1> <Val2> <Val3>`):")

if st.button("🔁 Replace Placeholders"):
    try:
        insert_values = re.findall(r'<(.*?)>', sql_inserts_raw)
        insert_values = [f"'{val}'" for val in insert_values]

        def replacer(match):
            nonlocal value_index
            if value_index >= len(insert_values):
                raise IndexError("🚫 More `?` placeholders than insert values.")
            value_index += 1
            return insert_values[value_index - 1]

        value_index = 0
        final_sql = re.sub(r'\?', replacer, sql_query)

        st.success("✅ Replacement complete!")
        st.code(final_sql, language='sql')

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
