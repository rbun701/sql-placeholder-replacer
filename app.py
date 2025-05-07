import streamlit as st
import re
from streamlit_copybutton import copybutton

st.set_page_config(page_title="SQL Placeholder Replacer", layout="wide")

st.title("🔄 Pega SQL Placeholder Replacer")
st.markdown("""
Paste your SQL query with `?` placeholders and the SQL Inserts (e.g. `<Val1> <Val2>`).
This tool will auto-replace each `?` with your values — in order.
""")

sql_query = st.text_area("Paste SQL Query with `?` placeholders:", height=300)
sql_inserts_raw = st.text_area("Paste SQL Inserts (e.g. `<Val1> <Val2>`):")

# Placeholder for results
result_area = st.empty()

# Buttons
col1, col2 = st.columns([1, 1])

if col1.button("🔁 Replace Placeholders"):
    try:
        insert_values = re.findall(r'<(.*?)>', sql_inserts_raw)
        insert_values = [f"'{val}'" for val in insert_values]

        counter = [0]
        def replacer(match):
            if counter[0] >= len(insert_values):
                raise IndexError("🚫 More `?` placeholders than insert values.")
            val = insert_values[counter[0]]
            counter[0] += 1
            return val

        final_sql = re.sub(r'\?', replacer, sql_query)

        st.success("✅ Replacement complete!")
        result_area.code(final_sql, language='sql')

        col3, col4 = st.columns([1, 1])
        with col3:
            st.download_button("📥 Download .sql file", final_sql, file_name="replaced_query.sql", mime="text/sql")
        with col4:
            copybutton(final_sql, "📋 Copy SQL to clipboard")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

if col2.button("🧹 Clear All"):
    st.rerun()
