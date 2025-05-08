import re

# --- SQL Keyword Casing ---
SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
    'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'DISTINCT',
    'UNION', 'ALL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CASE',
    'WHEN', 'THEN', 'ELSE', 'END', 'LIMIT', 'OFFSET', 'ESCAPE'
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
def format_clause_block(sql: str, clause: str) -> str:
    pattern = re.compile(rf'\b{clause}\b(.*?)(?=\bWHERE\b|\bHAVING\b|\bORDER BY\b|\bGROUP BY\b|\bFROM\b|\bLIMIT\b|$)', re.IGNORECASE | re.DOTALL)
    matches = pattern.finditer(sql)
    for match in matches:
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content.strip())
        aligned_block = align_clause_block(clause, expressions)
        sql = sql.replace(f"{clause}{content}", aligned_block)
    return sql


# --- Format SELECT blocks even inside subqueries ---
def align_all_select_blocks(sql: str) -> str:
    pattern = re.compile(r'(SELECT\s+.*?\bFROM\b)', re.IGNORECASE | re.DOTALL)
    def formatter(match):
        block = match.group(1)
        return format_clause_block(block, "SELECT")
    return pattern.sub(formatter, sql)


# --- GROUP BY and ORDER BY formatting ---
def align_group_and_order_blocks(sql: str) -> str:
    sql = format_clause_block(sql, "GROUP BY")
    sql = format_clause_block(sql, "ORDER BY")
    return sql


# --- Newline fix for major clauses ---
def newline_before_keywords(sql: str) -> str:
    keywords = [
        'FROM', 'WHERE', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN',
        'GROUP BY', 'ORDER BY', 'HAVING'
    ]
    for kw in keywords:
        # Insert a newline if keyword appears after a closing quote or number (no whitespace)
        pattern = re.compile(rf'(?<=[\w")])\s*({kw})\b', re.IGNORECASE)
        sql = pattern.sub(r'\n\1', sql)
    return sql


# --- Double spacing cleanup ---
def remove_extra_spaces(sql: str) -> str:
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    return '\n'.join(cleaned)


# --- Final beautification pipeline ---
def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = newline_before_keywords(sql)
    sql = align_all_select_blocks(sql)
    sql = align_group_and_order_blocks(sql)
    sql = remove_extra_spaces(sql)
    return sql
