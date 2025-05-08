
import re

SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
    'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'DISTINCT',
    'UNION', 'ALL', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'LIMIT', 'OFFSET', 'ESCAPE'
]

def uppercase_keywords(sql: str) -> str:
    for kw in sorted(SQL_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(rf'\b{re.escape(kw.lower())}\b', re.IGNORECASE)
        sql = pattern.sub(kw, sql)
    return sql

def align_clause_block(clause: str, expressions: list, indent: int = 2) -> str:
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
    padding_space = ' ' * indent
    for lhs, rhs in parsed:
        if rhs:
            padding = ' ' * (max_len - len(lhs))
            aligned.append(f'{padding_space}{lhs}{padding} AS {rhs},')
        else:
            aligned.append(f'{padding_space}{lhs},')
    if aligned:
        aligned[-1] = aligned[-1].rstrip(',')
    return f'{clause}\n' + '\n'.join(aligned)

def format_clause_block(sql: str, clause: str, indent: int = 2) -> str:
    pattern = re.compile(
        rf'\b{clause}\b(.*?)(?=\bWHERE\b|\bHAVING\b|\bORDER BY\b|\bGROUP BY\b|\bFROM\b|\bLIMIT\b|$)',
        re.IGNORECASE | re.DOTALL)
    matches = pattern.finditer(sql)
    for match in matches:
        content = match.group(1)
        expressions = re.split(r',(?=(?:[^()]*\([^()]*\))*[^()]*$)', content.strip())
        aligned_block = align_clause_block(clause.upper(), expressions, indent)
        sql = sql.replace(f"{clause}{content}", aligned_block)
    return sql

def align_all_select_blocks(sql: str) -> str:
    pattern = re.compile(r'(SELECT\s+.*?)(?=FROM)', re.IGNORECASE | re.DOTALL)
    def formatter(match):
        block = match.group(1)
        expressions = re.split(r',(?=(?:[^()]*\([^()]*\))*[^()]*$)', block[len('SELECT'):].strip())
        return align_clause_block("SELECT", expressions, indent=2)
    return pattern.sub(formatter, sql)

def align_group_and_order_blocks(sql: str) -> str:
    sql = format_clause_block(sql, "GROUP BY", indent=2)
    sql = format_clause_block(sql, "ORDER BY", indent=2)
    return sql

def insert_newlines(sql: str) -> str:
    keywords = ['FROM', 'LEFT OUTER JOIN', 'INNER JOIN', 'WHERE', 'GROUP BY', 'ORDER BY']
    for kw in keywords:
        sql = re.sub(rf'\s*{kw}', f'\n{kw}', sql, flags=re.IGNORECASE)
    return sql

def remove_extra_spaces(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        if ' AS ' in line:
            lines.append(line.rstrip())
        else:
            lines.append(re.sub(r'\s{2,}', ' ', line.strip()))
    return '\n'.join(lines)

def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = insert_newlines(sql)
    sql = align_all_select_blocks(sql)
    sql = align_group_and_order_blocks(sql)
    sql = remove_extra_spaces(sql)
    return sql
