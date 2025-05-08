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


# --- Alignment Helpers ---
def align_clause_block(clause: str, expressions: list) -> str:
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
    for lhs, rhs in parsed:
        if rhs:
            padding = ' ' * (max_len - len(lhs))
            aligned.append(f'  {lhs}{padding} AS {rhs},')
        else:
            aligned.append(f'  {lhs},')
    if aligned:
        aligned[-1] = aligned[-1].rstrip(',')
    return f'{clause}\n' + '\n'.join(aligned)


def format_clause_block(sql: str, clause: str) -> str:
    pattern = re.compile(rf'\b{clause}\b(.*?)(?=\bWHERE\b|\bHAVING\b|\bORDER BY\b|\bGROUP BY\b|\bFROM\b|\bLIMIT\b|$)', re.IGNORECASE | re.DOTALL)
    matches = pattern.finditer(sql)
    for match in matches:
        content = match.group(1)
        expressions = re.split(r',(?![^()]*\))', content.strip())
        aligned_block = align_clause_block(clause.upper(), expressions)
        sql = sql.replace(f"{clause}{content}", aligned_block)
    return sql


# --- SELECT formatter (with subquery support) ---
def align_all_select_blocks(sql: str) -> str:
    pattern = re.compile(r'(SELECT\s+.*?\bFROM\b)', re.IGNORECASE | re.DOTALL)
    def formatter(match):
        block = match.group(1)
        return format_clause_block(block, "SELECT")
    return pattern.sub(formatter, sql)


# --- Optional GROUP BY and ORDER BY alignment ---
def align_group_and_order_blocks(sql: str) -> str:
    sql = format_clause_block(sql, "GROUP BY")
    sql = format_clause_block(sql, "ORDER BY")
    return sql


# --- Whitespace Cleaner ---
def remove_extra_spaces(sql: str) -> str:
    cleaned = []
    for line in sql.splitlines():
        if ' AS ' in line:
            cleaned.append(line.rstrip())
        else:
            cleaned.append(re.sub(r'\s{2,}', ' ', line.strip()))
    return '\n'.join(cleaned)


# --- Final Exported Function ---
def beautify_sql(sql: str) -> str:
    sql = uppercase_keywords(sql)
    sql = align_all_select_blocks(sql)
    sql = align_group_and_order_blocks(sql)
    sql = remove_extra_spaces(sql)
    return sql
