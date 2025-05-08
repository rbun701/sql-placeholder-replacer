import re

# --- SQL Keyword Casing ---
SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
    'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'DISTINCT',
    'UNION', 'ALL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CASE',
    'WHEN', 'THEN', 'ELSE', 'END', 'LIMIT', 'OFFSET', 'ESCAPE', 'PARTITION BY', 'WITH'
]

def uppercase_keywords(sql: str) -> str:
    for kw in sorted(SQL_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(rf'\b{re.escape(kw.lower())}\b', re.IGNORECASE)
        sql = pattern.sub(kw, sql)
    return sql

# --- Format SELECT expressions and align AS columns ---
def align_clause_block(clause: str, expressions: list, indent_level=1) -> str:
    parsed = []
    max_len = 0
    for line in expressions:
        parts = re.split(r'\s+AS\s+', line.strip(), flags=re.IGNORECASE)
        if len(parts) == 2:
            lhs, rhs = parts
            lhs = lhs.strip()
            rhs = rhs.strip()
            parsed.append((lhs, rhs))
            max_len = max(max_len, len(lhs))
        else:
            parsed.append((line.strip(), None))
            max_len = max(max_len, len(line.strip()))
    aligned = []
    indent = '  ' * indent_level
    for lhs, rhs in parsed:
        if rhs:
            padding = ' ' * (max_len - len(lhs))
            aligned.append(f'{indent}{lhs}{padding} AS {rhs},')
        else:
            aligned.append(f'{indent}{lhs},')
    if aligned:
        aligned[-1] = aligned[-1].rstrip(',')
    return f'{clause.upper()}\n' + '\n'.join(aligned)

# --- Apply alignment logic to each clause ---
def format_clause_block(sql: str, clause: str, indent_level=1) -> str:
    pattern = re.compile(
        rf'\b{clause}\b(.*?)(?=\n\b(?:SELECT|FROM|WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|INNER JOIN)\b|$)',
        re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.finditer(sql)
    for match in matches:
        full = match.group(0)
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content.strip())
        aligned = align_clause_block(clause, expressions, indent_level)
        sql = sql.replace(full, aligned)
    return sql


# --- Format SELECT blocks even inside subqueries ---
def align_all_select_blocks(sql: str) -> str:
    pattern = re.compile(r'(SELECT\s+.*?\bFROM\b)', re.IGNORECASE | re.DOTALL)
    def formatter(match):
        block = match.group(1)
        return format_clause_block(block, "SELECT", indent_level=1)
    return pattern.sub(formatter, sql)

# --- Ensure newline before major keywords ---
def newline_before_keywords(sql: str) -> str:
    # Sort by length to catch "ORDER BY" before "ORDER"
    keywords = sorted([
        'PARTITION BY', 'GROUP BY', 'ORDER BY', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'INNER JOIN',
        'FROM', 'WHERE', 'HAVING', 'JOIN'
    ], key=len, reverse=True)

    for kw in keywords:
        # Only insert newline when keyword is preceded by a character like ), ", or alphanum (but NOT already on its own line)
        pattern = re.compile(rf'(?<=[\w")])\s+({re.escape(kw)})\b', re.IGNORECASE)
        sql = pattern.sub(r'\n\1', sql)
    return sql

def format_joins(sql: str) -> str:
    pattern = re.compile(r'(LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|INNER\s+JOIN|JOIN)\s+(.*?)\s+ON\s+(.*?)(?=\b(LEFT|RIGHT|FULL|INNER|JOIN|WHERE|GROUP BY|ORDER BY|HAVING|$))', re.IGNORECASE | re.DOTALL)
    def reformat(match):
        join_type = match.group(1).upper()
        table = match.group(2).strip()
        on_clause = match.group(3).strip()
        # Break ON clause by AND
        on_lines = re.split(r'\bAND\b', on_clause)
        on_lines = [f'    AND {line.strip()}' if idx != 0 else f'  ON {line.strip()}' for idx, line in enumerate(on_lines)]
        return f'{join_type} {table}\n' + '\n'.join(on_lines)

    return pattern.sub(reformat, sql)


# --- Clean up extra spaces ---
def remove_extra_spaces(sql: str) -> str:
    # Clean up spacing within each line
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    
    # Remove double (or more) blank lines
    cleaned_sql = '\n'.join(cleaned)
    cleaned_sql = re.sub(r'\n{3,}', '\n\n', cleaned_sql)  # reduce 3+ blank lines to just 1
    return cleaned_sql


# --- Final beautification pipeline ---
def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = newline_before_keywords(sql)
    sql = format_joins(sql)
    sql = align_all_select_blocks(sql)
    sql = format_clause_block(sql, "GROUP BY", indent_level=2)
    sql = format_clause_block(sql, "ORDER BY", indent_level=2)
    sql = remove_extra_spaces(sql)
    return sql
