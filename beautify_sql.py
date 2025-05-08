import re

SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
    'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'DISTINCT',
    'UNION', 'ALL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'LIMIT', 'OFFSET', 'ESCAPE', 'PARTITION BY', 'WITH'
]

def uppercase_keywords(sql: str) -> str:
    for kw in sorted(SQL_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE)
        sql = pattern.sub(kw, sql)
    return sql

def newline_before_keywords(sql: str) -> str:
    keywords = sorted([
        'PARTITION BY', 'GROUP BY', 'ORDER BY', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'INNER JOIN',
        'FROM', 'WHERE', 'HAVING', 'JOIN'
    ], key=len, reverse=True)

    for kw in keywords:
        pattern = re.compile(rf'(?<!\n)(?<!\w)(\s*)({re.escape(kw)})(?!\w)', re.IGNORECASE)
        sql = pattern.sub(r'\n\2', sql)
    return sql

def align_clause_block(clause: str, expressions: list, indent_level=1) -> str:
    parsed, max_len = [], 0
    for line in expressions:
        parts = re.split(r'\s+AS\s+', line.strip(), flags=re.IGNORECASE)
        lhs, rhs = (parts + [None])[:2]
        lhs = lhs.strip()
        if rhs: rhs = rhs.strip()
        parsed.append((lhs, rhs))
        max_len = max(max_len, len(lhs))

    indent = '  ' * indent_level
    lines = [
        f"{indent}{lhs}{' ' * (max_len - len(lhs))} AS {rhs}," if rhs else f"{indent}{lhs},"
        for lhs, rhs in parsed
    ]
    if lines:
        lines[-1] = lines[-1].rstrip(',')
    return f"{clause.upper()}\n" + '\n'.join(lines)

def format_clause_block(sql: str, clause: str, indent_level=1) -> str:
    pattern = re.compile(
        rf'\b{clause}\b(.*?)(?=\n\b(?:SELECT|FROM|WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|INNER JOIN)\b|$)',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(sql):
        full = match.group(0)
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content.strip())
        aligned = align_clause_block(clause, expressions, indent_level)
        sql = sql.replace(full, aligned)
    return sql

def format_joins(sql: str) -> str:
    pattern = re.compile(
        r'(LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|INNER\s+JOIN|JOIN)\s+(.*?)\s+ON\s+(.*?)(?=\b(LEFT|RIGHT|FULL|INNER|JOIN|WHERE|GROUP BY|ORDER BY|HAVING|$))',
        re.IGNORECASE | re.DOTALL
    )

    def reformat(match):
        join_type, table, on_clause = match.groups()[:3]
        on_lines = re.split(r'\bAND\b', on_clause)
        formatted = [f'    AND {line.strip()}' if i else f'  ON {line.strip()}' for i, line in enumerate(on_lines)]
        return f'{join_type.upper()} {table.strip()}\n' + '\n'.join(formatted)

    return pattern.sub(reformat, sql)

def remove_extra_spaces(sql: str) -> str:
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    cleaned_sql = '\n'.join(cleaned)
    return re.sub(r'\n{3,}', '\n\n', cleaned_sql)

def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = newline_before_keywords(sql)
    sql = format_joins(sql)
    sql = align_clause_block("SELECT", re.split(r',(?![^()]*\))', sql), indent_level=1)
    sql = format_clause_block(sql, "GROUP BY", indent_level=2)
    sql = format_clause_block(sql, "ORDER BY", indent_level=2)
    sql = format_clause_block(sql, "WHERE", indent_level=2)
    sql = remove_extra_spaces(sql)
    return sql
