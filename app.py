import streamlit as st
import re
import streamlit.components.v1 as components
import sqlparse

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
        formatted_sql = sqlparse.format(final_sql, reindent=True, keyword_case='upper')
        formatted_sql = re.sub(r'[ ]{2,}', ' ', formatted_sql)
        formatted_sql = '\n'.join(line.strip() for line in formatted_sql.splitlines())

        st.success("✅ Replacement complete!")
        result_area.code(formatted_sql, language='sql')

        col3, col4 = st.columns([1, 1])
        with col3:
            st.download_button(
                "📥 Download .sql file",
                formatted_sql,
                file_name="replaced_query.sql",
                mime="text/sql"
            )

        with col4:
            st.markdown("### 📋 Copy to clipboard")
            components.html(
                f"""
                <textarea id="sqlText" style="width:100%; height:120px;">{final_sql}</textarea>
                <button onclick="navigator.clipboard.writeText(document.getElementById('sqlText').value)"
                        style="margin-top:10px;padding:8px 16px;font-size:16px;">
                    ✅ Copy SQL
                </button>
                """,
                height=200,
            )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

if col2.button("🧹 Clear All"):
    st.rerun()
