import re

SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
    'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'DISTINCT',
    'UNION', 'UNION ALL', 'EXCEPT', 'INTERSECT',  # <-- Add here
    'ALL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'LIMIT', 'OFFSET', 'ESCAPE', 'PARTITION BY', 'WITH'
]

def uppercase_keywords(sql: str) -> str:
    multi_word_keywords = [
        'LEFT OUTER JOIN', 'RIGHT OUTER JOIN', 'FULL OUTER JOIN',
        'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'INNER JOIN', 'OUTER JOIN',
        'PARTITION BY', 'ORDER BY', 'GROUP BY',
        'UNION ALL'  # <-- Add here
    ]

    single_word_keywords = [
        'SELECT', 'FROM', 'WHERE', 'HAVING', 'JOIN', 'ON', 'AS', 'AND', 'OR', 'NOT',
        'IN', 'IS', 'NULL', 'DISTINCT', 'UNION', 'ALL', 'EXCEPT', 'INTERSECT',  # <-- Add more here
        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'LIMIT', 'OFFSET', 'ESCAPE', 'WITH'
    ]


    for phrase in sorted(multi_word_keywords, key=len, reverse=True):
        sql = re.sub(re.escape(phrase), phrase.upper(), sql, flags=re.IGNORECASE)

    for word in sorted(single_word_keywords, key=len, reverse=True):
        sql = re.sub(rf'\b{word}\b', word.upper(), sql, flags=re.IGNORECASE)

    return sql


def newline_before_keywords(sql: str) -> str:
    keywords = sorted([
        'LEFT OUTER JOIN', 'RIGHT OUTER JOIN', 'FULL OUTER JOIN',
        'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'INNER JOIN', 'OUTER JOIN',
        'PARTITION BY', 'GROUP BY', 'ORDER BY',
        'UNION ALL', 'UNION', 'EXCEPT', 'INTERSECT',  # <-- Added here
        'FROM', 'WHERE', 'HAVING', 'JOIN'
    ], key=len, reverse=True)
    
    for kw in keywords:
        # Ensure newline appears before the full keyword, preserving it as one unit
        # pattern = re.compile(rf'(?<!\n)(\s*)\b({re.escape(kw)})\b(?!\w)', re.IGNORECASE)
        # pattern = re.compile(rf'(?<!\n)(\s*)\b({re.escape(kw)})(?=\b|\s|[(),])', re.IGNORECASE)
        pattern = re.compile(rf'(?<!\n)(\s*)\b{re.escape(kw)}\b(?=\s|\(|$)', re.IGNORECASE)
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
        rf'\b{clause}\b(.*?)(?=\n?\b(?:SELECT|FROM|WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|LEFT OUTER JOIN|RIGHT OUTER JOIN|FULL OUTER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|INNER JOIN|JOIN)\b|--|;|$)',
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(sql):
        full = match.group(0)
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content)
        aligned = align_clause_block(clause, expressions, indent_level)
        sql = sql.replace(full, aligned)
    return sql

def format_joins(sql: str) -> str:
    pattern = re.compile(
        r'(LEFT\s+OUTER\s+JOIN|RIGHT\s+OUTER\s+JOIN|FULL\s+OUTER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|INNER\s+JOIN|JOIN)\s+(.*?)\s+ON\s+(.*?)(?=\b(LEFT|RIGHT|FULL|INNER|JOIN|WHERE|GROUP BY|ORDER BY|HAVING|$))',
        re.IGNORECASE | re.DOTALL
    )


    def reformat(match):
        join_type, table, on_clause = match.groups()[:3]
        on_lines = re.split(r'\bAND\b', on_clause)
        formatted = [f'    AND {line.strip()}' if i else f'  ON {line.strip()}' for i, line in enumerate(on_lines)]
        return f'{join_type.upper()} {table.strip()}\n' + '\n'.join(formatted)

    return pattern.sub(reformat, sql)


def format_union_clauses(sql: str) -> str:
    for kw in ['UNION ALL', 'UNION', 'EXCEPT', 'INTERSECT']:
        # sql = re.sub(rf'\s*({kw})\s*', rf'\n{kw}\n', sql, flags=re.IGNORECASE)
        sql = re.sub(rf'(?<!\w)\s*({re.escape(kw)})\s*(?!\w)', rf'\n\1\n', sql, flags=re.IGNORECASE)
    return sql


def format_expression_clause(sql: str, clause: str, indent_level=1) -> str:
    pattern = re.compile(
        rf'\b{clause}\b(.*?)(?=\b(?:SELECT|FROM|WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN|INNER JOIN)\b|$)',
        re.IGNORECASE | re.DOTALL,
    )
    matches = pattern.finditer(sql)
    for match in matches:
        full = match.group(0)
        content = match.group(1)
        expressions = re.split(r'\bAND\b', content)
        indent = '  ' * indent_level
        formatted = f'\n{clause.upper()}\n' + '\n'.join([f'{indent}{line.strip()}' for line in expressions])
        sql = sql.replace(full, formatted)
    return sql

def remove_extra_spaces(sql: str) -> str:
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    cleaned_sql = '\n'.join(cleaned)
    return re.sub(r'\n{3,}', '\n\n', cleaned_sql)

def insert_spacing_between_clauses(sql: str) -> str:
    clauses = ['WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
    for clause in clauses:
        sql = re.sub(rf'(\n{clause}\b)', r'\n\1', sql, flags=re.IGNORECASE)
    return sql

def beautify_sql(sql: str) -> str:
    try:
        sql = uppercase_keywords(sql)
        sql = newline_before_keywords(sql)
        sql = format_clause_block(sql, "SELECT", indent_level=1)
        sql = format_expression_clause(sql, "WHERE", indent_level=4)
        sql = format_expression_clause(sql, "HAVING", indent_level=4)
        sql = format_clause_block(sql, "GROUP BY", indent_level=4)
        sql = format_clause_block(sql, "ORDER BY", indent_level=4)
        sql = format_joins(sql)
        sql = format_union_clauses(sql)
        sql = remove_extra_spaces(sql)
        sql = insert_spacing_between_clauses(sql)
        return sql
    except Exception as e:
        return f"-- Failed to beautify SQL due to: {e}\n\n{sql}"
