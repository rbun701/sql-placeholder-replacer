import re

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
    return f'\n{clause.upper()}\n' + '\n'.join(aligned)

def format_clause_block(sql: str, clause: str) -> str:
    pattern = re.compile(rf'(?i)\b{clause}\b(.*?)(?=\b(FROM|WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|$))', re.DOTALL)
    matches = pattern.finditer(sql)
    for match in matches:
        full = match.group(0)
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content.strip())
        aligned = align_clause_block(clause, expressions)
        sql = sql.replace(full, aligned)
    return sql

def align_all_select_blocks(sql: str) -> str:
    return format_clause_block(sql, "SELECT")

def align_group_and_order_blocks(sql: str) -> str:
    sql = format_clause_block(sql, "GROUP BY")
    sql = format_clause_block(sql, "ORDER BY")
    return sql

def newline_before_keywords(sql: str) -> str:
    keywords = [
        'FROM', 'WHERE', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN',
        'GROUP BY', 'ORDER BY', 'HAVING'
    ]
    for kw in sorted(keywords, key=len, reverse=True):
        pattern = re.compile(rf'\s*({kw})\b', re.IGNORECASE)
        sql = pattern.sub(r'\n\1', sql)
    return sql

def remove_extra_spaces(sql: str) -> str:
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    return '\n'.join(cleaned)

def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = align_all_select_blocks(sql)
    sql = align_group_and_order_blocks(sql)
    sql = newline_before_keywords(sql)  # FIXED: move after select formatting
    sql = remove_extra_spaces(sql)
    return sql
