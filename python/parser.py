"""
Natural Language to SQL Parser - Complete Pipeline
===================================================

Architecture (matching system workflow diagram):

    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Natural      │────▶│    LEXER     │────▶│    PARSER    │────▶│     SQL      │
    │ Language     │     │  (Tokenize)  │     │   (AST)      │     │  Generator   │
    └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘

This module provides TWO parsing methods:
1. NEW: Lexer → Parser → AST → SQL (proper compiler architecture)
2. LEGACY: English → DSL → AST → SQL (regex-based, for backward compatibility)
"""

import re
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Try to import new pipeline modules
try:
    from lexer import Lexer, Token, TokenType, tokenize
    from syntax_parser import Parser as SyntaxParser, ast_to_dict as new_ast_to_dict
    from pipeline import NLToSQLPipeline, nl_to_sql, process_text
    HAS_NEW_PIPELINE = True
except ImportError:
    HAS_NEW_PIPELINE = False

# =========================================================
#                   ENGLISH → DSL
# =========================================================

def normalize_operators(text):
    """Normalize natural language operators to SQL operators."""
    t = text.lower()

    # equal variations
    t = t.replace("is equal to", "=")
    t = t.replace("equal to", "=")
    t = t.replace("equals", "=")
    t = t.replace("equal", "=")
    t = t.replace("same as", "=")

    # greater than / less than variations
    t = t.replace("greater than or equal to", ">=")
    t = t.replace("less than or equal to", "<=")
    t = t.replace("greater than", ">")
    t = t.replace("less than", "<")

    return t


def english_to_dsl(text):
    """Convert English natural language to SQL DSL."""
    text = normalize_operators(text)
    text = text.lower()
    
    # Rule 1: SELECT all (...) from table WITH optional WHERE
    m = re.match(
        r"(select|show|list) all(?: (\w+))? (?:of|from) (\w+)(?:\s+where\s+(\w+)\s*(>=|<=|=|>|<)\s*(\d+))?",
        text,
        flags=re.IGNORECASE
    )
    if m:
        col = m.group(2)
        table = m.group(3)
        where_col = m.group(4)
        operator = m.group(5)
        where_val = m.group(6)
        if col:
            query = f"SELECT {col} FROM {table}"
        else:
            query = f"SELECT * FROM {table}"
        if where_col:
            query += f" WHERE {where_col} {operator} {where_val}"
        return query

    # Rule 2: SELECT with condition (>, <, =)
    m = re.match(r"(select|show|list) (?:all\s+)? (\w+) from (\w+) where (\w+) (>|<|=) (\d+)", text)
    if m:
        column = m.group(2)
        table = m.group(3)
        cond_col = m.group(4)
        op = m.group(5)
        val = m.group(6)
        return f"SELECT {column} FROM {table} WHERE {cond_col} {op} {val}"

    # Rule 3: COUNT queries
    m = re.match(
        r"(count|how many)\s+(\w+)(?:\s+from\s+(\w+))?(?:\s+where\s+(\w+)\s*(=|>|<)\s*(\d+))?",
        text,
        flags=re.IGNORECASE
    )
    if m:
        col = m.group(2)
        table = m.group(3)
        where_col = m.group(4)
        op = m.group(5)
        val = m.group(6)

        if table is None:
            table = col
            col = None

        query = (
            f"SELECT COUNT({col}) FROM {table}"
            if col else
            f"SELECT COUNT(*) FROM {table}"
        )
        if where_col:
            query += f" WHERE {where_col} {op} {val}"

        return query

    # Rule 4: SUM with optional column and optional WHERE
    m = re.match(
        r"(sum|total)(?: (\w+))? from (\w+)(?: where (\w+)\s*=\s*(\w+))?",
        text,
        flags=re.IGNORECASE
    )
    if m:
        col = m.group(2)
        table = m.group(3)
        where_col = m.group(4)
        where_val = m.group(5)

        if col:
            query = f"SELECT SUM({col}) FROM {table}"
        else:
            query = f"SELECT SUM(*) FROM {table}"

        if where_col:
            query += f" WHERE {where_col} = {where_val}"

        return query

    # Rule 5: ORDER BY with WHERE
    m = re.match(
        r"(select|show) all (\w+) where (\w+) (>=|<=|>|<|=) (\w+) order by(?: (\w+))?(?: (asc|desc))?",
        text
    )
    if m:
        table = m.group(2)
        cond_col, op, val = m.group(3), m.group(4), m.group(5)
        order_col = m.group(6) if m.group(6) else "id"
        order = m.group(7).upper() if m.group(7) else ""
        return f"SELECT * FROM {table} WHERE {cond_col} {op} {val} ORDER BY {order_col} {order}".strip()

    # Rule 5b: ORDER BY without WHERE
    m = re.match(
        r"(select|show) all (\w+) order by(?: (\w+))?(?: (asc|desc))?",
        text
    )
    if m:
        table = m.group(2)
        order_col = m.group(3) if m.group(3) else "id"
        order = m.group(4).upper() if m.group(4) else ""
        return f"SELECT * FROM {table} ORDER BY {order_col} {order}".strip()

    # Rule 6: GROUP BY
    m = re.match(
        r"(select|show) (\w+(?:, \w+)*) from (\w+) group by (\w+)",
        text,
        flags=re.IGNORECASE
    )
    if m:
        cols = m.group(2)
        table = m.group(3)
        group_col = m.group(4)
        cols = ", ".join([c.strip() for c in cols.split(",")])
        return f"SELECT {cols} FROM {table} GROUP BY {group_col}"

    # Rule 7: Multiple conditions (AND/OR)
    m = re.match(
        r"(select|show|display)(?:\s+(all))?(?:\s+([\w, ]+))?(?:\s+from)?\s+(\w+)\s+where\s+(\w+)\s*(>|<|=)\s*(\d+)\s+(and|or)\s+(\w+)\s*(>|<|=)\s*(\d+)",
        text,
        re.IGNORECASE
    )
    if m:
        groups = m.groups()
        all_kw = groups[1]
        columns = groups[2]
        table = groups[3]
        col1, op1, val1 = groups[4], groups[5], groups[6]
        logic = groups[7]
        col2, op2, val2 = groups[8], groups[9], groups[10]

        if all_kw or not columns:
            select_part = "SELECT *"
        else:
            cols = ",".join([c.strip() for c in columns.split(",")])
            select_part = f"SELECT {cols}"

        query = (
            f"{select_part} FROM {table} "
            f"WHERE {col1} {op1} {val1} {logic.upper()} {col2} {op2} {val2}"
        )
        return query

    # Rule 8: INSERT
    m = re.match(r"(insert into|add new row into)\s+(\w+)\s+values\s+(.+)", text, re.IGNORECASE)
    if m:
        _, table, values = m.groups()
        return f"INSERT INTO {table} VALUES ({values})"

    # Rule 9: UPDATE
    m = re.match(r"(update|change)\s+(\w+)\s+set\s+(\w+)\s*=\s*([\w' ]+)\s+where\s+(\w+)\s*=\s*([\w' ]+)", text, re.IGNORECASE)
    if m:
        _, table, col_set, val_set, col_where, val_where = m.groups()
        return f"UPDATE {table} SET {col_set} = {val_set} WHERE {col_where} = {val_where}"

    # Rule 10: DELETE
    m = re.match(r"(delete from|remove from)\s+(\w+)\s+where\s+(\w+)\s*(=|>|<)\s*([\w' ]+)", text, re.IGNORECASE)
    if m:
        _, table, col, op, val = m.groups()
        return f"DELETE FROM {table} WHERE {col} {op} {val}"

    # Rule 11: DROP COLUMN
    m = re.match(r"(delete|remove)\s+(column|columns|col)\s+([\w, ]+)\s+from\s+(\w+)", text, re.IGNORECASE)
    if m:
        _, _, cols, table = m.groups()
        col_list = [c.strip() for c in cols.split(",")]
        drop_parts = ", ".join([f"DROP COLUMN {c}" for c in col_list])
        return f"ALTER TABLE {table} {drop_parts}"

    # Rule 12: LIKE
    m = re.match(r"(find|search)\s+(\w+)\s+where\s+(\w+)\s+(contains|like)\s+'(.+)'", text, re.IGNORECASE)
    if m:
        _, table, col, _, val = m.groups()
        return f"SELECT * FROM {table} WHERE {col} LIKE '%{val}%'"

    # Rule 13: BETWEEN
    m = re.match(r"select\s+(\w+)\s+where\s+(\w+)\s+between\s+(\d+)\s+and\s+(\d+)", text, re.IGNORECASE)
    if m:
        table, col, v1, v2 = m.groups()
        return f"SELECT * FROM {table} WHERE {col} BETWEEN {v1} AND {v2}"

    # Rule 14: IN
    m = re.match(r"select\s+(\w+)\s+where\s+(\w+)\s+in\s+(.+)", text, re.IGNORECASE)
    if m:
        table, col, vals = m.groups()
        val_list = ",".join(v.strip() for v in vals.split(","))
        return f"SELECT * FROM {table} WHERE {col} IN ({val_list})"

    # Rule 15: DISTINCT
    m = re.match(r"select\s+(distinct|unique)\s+(\w+)\s+from\s+(\w+)", text, re.IGNORECASE)
    if m:
        _, col, table = m.groups()
        return f"SELECT DISTINCT {col} FROM {table}"

    # Semantic rules for more natural language
    # Rule: "Show me X" / "Give me X"
    m = re.match(r"(?:show|give|display|get)\s+me\s+(?:all\s+)?(\w+)", text, re.IGNORECASE)
    if m:
        table = m.group(1)
        return f"SELECT * FROM {table}"

    # Rule: "Get all X"
    m = re.match(r"get\s+all\s+(\w+)", text, re.IGNORECASE)
    if m:
        table = m.group(1)
        return f"SELECT * FROM {table}"

    return "No matching rule found"


# =========================================================
#                   AST CLASSES
# =========================================================

class AST:
    pass

class Select(AST):
    def __init__(self, columns, table, where=None, order=None, group=None, func=None, distinct=False):
        self.columns = columns
        self.table = table
        self.where = where
        self.order = order
        self.group = group
        self.func = func
        self.distinct = distinct

class Where(AST):
    def __init__(self, left):
        self.left = left

class Condition(AST):
    def __init__(self, column, op, value):
        self.column = column
        self.op = op
        self.value = value

class And(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Or(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Between(AST):
    def __init__(self, column, low, high):
        self.column = column
        self.low = low
        self.high = high

class In(AST):
    def __init__(self, column, values):
        self.column = column
        self.values = values

class Like(AST):
    def __init__(self, column, pattern):
        self.column = column
        self.pattern = pattern

class Order(AST):
    def __init__(self, column, direction="ASC"):
        self.column = column
        self.direction = direction

class Group(AST):
    def __init__(self, column):
        self.column = column

class CountFunc(AST):
    def __init__(self, column):
        self.column = column

class SumFunc(AST):
    def __init__(self, column):
        self.column = column

class Insert(AST):
    def __init__(self, table, values):
        self.table = table
        self.values = values

class Update(AST):
    def __init__(self, table, col_set, val_set, cond_col, cond_val):
        self.table = table
        self.col_set = col_set
        self.val_set = val_set
        self.cond_col = cond_col
        self.cond_val = cond_val

class Delete(AST):
    def __init__(self, table, column, op, value):
        self.table = table
        self.column = column
        self.op = op
        self.value = value

class DropColumn(AST):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns


# =========================================================
#                   DSL → AST PARSER
# =========================================================

def parse_dsl(t):
    """Parse DSL string into AST."""
    t = t.strip()

    # INSERT
    m = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", t, re.IGNORECASE)
    if m:
        return Insert(m.group(1), [v.strip() for v in m.group(2).split(",")])

    # UPDATE
    m = re.match(r"UPDATE (\w+) SET (\w+)\s*=\s*(.+?) WHERE (\w+)\s*=\s*(.+)", t, re.IGNORECASE)
    if m:
        return Update(m.group(1), m.group(2), m.group(3).strip(), m.group(4), m.group(5).strip())

    # DELETE
    m = re.match(r"DELETE FROM (\w+) WHERE (\w+)\s*(=|>|<)\s*(.+)", t, re.IGNORECASE)
    if m:
        return Delete(m.group(1), m.group(2), m.group(3), m.group(4))

    # DROP COLUMN
    m = re.match(r"ALTER TABLE (\w+) (DROP COLUMN .+)", t, re.IGNORECASE)
    if m:
        cols = [c.replace("DROP COLUMN", "").strip() for c in m.group(2).split(",")]
        return DropColumn(m.group(1), cols)

    # DISTINCT
    m = re.match(r"SELECT DISTINCT (\w+) FROM (\w+)", t, re.IGNORECASE)
    if m:
        return Select([m.group(1)], m.group(2), distinct=True)

    # COUNT
    m = re.match(r"SELECT COUNT\((\w+|\*)\) FROM (\w+)", t)
    if m:
        col = None if m.group(1) == "*" else m.group(1)
        return Select(["COUNT"], m.group(2), func=CountFunc(col))

    # SUM
    m = re.match(r"SELECT SUM\((\w+|\*)\) FROM (\w+)", t)
    if m:
        col = None if m.group(1) == "*" else m.group(1)
        return Select(["SUM"], m.group(2), func=SumFunc(col))

    # BASIC SELECT
    m = re.match(r"SELECT (.+) FROM (\w+)", t)
    if not m:
        return {"error": "Could not parse DSL"}

    columns_raw = m.group(1)
    table = m.group(2)
    columns = ["*"] if columns_raw == "*" else [c.strip() for c in columns_raw.split(",")]

    where_node = None

    # BETWEEN
    m = re.search(r"WHERE (\w+) BETWEEN (\d+) AND (\d+)", t)
    if m:
        where_node = Where(Between(m.group(1), m.group(2), m.group(3)))

    # IN
    m = re.search(r"WHERE (\w+) IN \((.+)\)", t)
    if m:
        where_node = Where(In(m.group(1), [v.strip() for v in m.group(2).split(",")]))

    # LIKE
    m = re.search(r"WHERE (\w+) LIKE '(.+)'", t)
    if m:
        where_node = Where(Like(m.group(1), m.group(2)))

    # AND/OR
    m = re.search(r"WHERE (\w+) (>|<|=) (\w+) (AND|OR) (\w+) (>|<|=) (\w+)", t)
    if m:
        c1 = Condition(m.group(1), m.group(2), m.group(3))
        c2 = Condition(m.group(5), m.group(6), m.group(7))
        where_node = Where(And(c1, c2) if m.group(4) == "AND" else Or(c1, c2))

    # SIMPLE WHERE
    if where_node is None:
        m = re.search(r"WHERE (\w+)\s*(=|>|<)\s*(.+?)(?:\s+ORDER|\s+GROUP|$)", t)
        if m:
            where_node = Where(Condition(m.group(1), m.group(2), m.group(3).strip()))

    # ORDER
    order_node = None
    m = re.search(r"ORDER BY (\w+)(?: (ASC|DESC))?", t)
    if m:
        order_node = Order(m.group(1), m.group(2) if m.group(2) else "ASC")

    # GROUP
    group_node = None
    m = re.search(r"GROUP BY (\w+)", t)
    if m:
        group_node = Group(m.group(1))

    return Select(columns, table, where_node, order_node, group_node)


def ast_to_dict(node):
    """Convert AST node to dictionary for JSON serialization."""
    if node is None:
        return None
    if isinstance(node, dict):
        return node

    if isinstance(node, Select):
        return {
            "type": "Select",
            "columns": node.columns,
            "table": node.table,
            "where": ast_to_dict(node.where),
            "order": ast_to_dict(node.order),
            "group": ast_to_dict(node.group),
            "func": ast_to_dict(node.func),
            "distinct": node.distinct
        }

    if isinstance(node, Where):
        return {"type": "Where", "expr": ast_to_dict(node.left)}

    if isinstance(node, Condition):
        return {"type": "Condition", "col": node.column, "op": node.op, "value": node.value}

    if isinstance(node, And):
        return {"type": "AND", "left": ast_to_dict(node.left), "right": ast_to_dict(node.right)}

    if isinstance(node, Or):
        return {"type": "OR", "left": ast_to_dict(node.left), "right": ast_to_dict(node.right)}

    if isinstance(node, Between):
        return {"type": "Between", "column": node.column, "low": node.low, "high": node.high}

    if isinstance(node, In):
        return {"type": "IN", "column": node.column, "values": node.values}

    if isinstance(node, Like):
        return {"type": "LIKE", "column": node.column, "pattern": node.pattern}

    if isinstance(node, Order):
        return {"type": "Order", "column": node.column, "direction": node.direction}

    if isinstance(node, Group):
        return {"type": "Group", "column": node.column}

    if isinstance(node, Insert):
        return {"type": "Insert", "table": node.table, "values": node.values}

    if isinstance(node, Update):
        return {
            "type": "Update",
            "table": node.table,
            "set_col": node.col_set,
            "set_val": node.val_set,
            "cond_col": node.cond_col,
            "cond_val": node.cond_val
        }

    if isinstance(node, Delete):
        return {"type": "Delete", "table": node.table, "column": node.column, "op": node.op, "value": node.value}

    if isinstance(node, DropColumn):
        return {"type": "DropColumn", "table": node.table, "columns": node.columns}

    if isinstance(node, CountFunc):
        return {"type": "CountFunc", "column": node.column}

    if isinstance(node, SumFunc):
        return {"type": "SumFunc", "column": node.column}

    return str(node)


# =========================================================
#                   AST → SQL GENERATOR
# =========================================================

def ast_to_sql(node):
    """Convert AST node to SQL string."""
    if node is None:
        return ""

    if isinstance(node, dict):
        if "error" in node:
            return f"-- Error: {node['error']}"
        return str(node)

    # SELECT statement
    if isinstance(node, Select):
        sql = "SELECT "

        # Handle DISTINCT
        if node.distinct:
            sql += "DISTINCT "

        # Handle aggregate functions (COUNT, SUM)
        if node.func:
            if isinstance(node.func, CountFunc):
                col = node.func.column if node.func.column else "*"
                sql += f"COUNT({col})"
            elif isinstance(node.func, SumFunc):
                col = node.func.column if node.func.column else "*"
                sql += f"SUM({col})"
        else:
            # Regular columns
            sql += ", ".join(node.columns)

        sql += f" FROM {node.table}"

        # WHERE clause
        if node.where:
            sql += " " + generate_where(node.where)

        # GROUP BY clause
        if node.group:
            sql += f" GROUP BY {node.group.column}"

        # ORDER BY clause
        if node.order:
            sql += f" ORDER BY {node.order.column}"
            if node.order.direction:
                sql += f" {node.order.direction}"

        return sql.strip()

    # INSERT statement
    if isinstance(node, Insert):
        values = ", ".join(str(v) for v in node.values)
        return f"INSERT INTO {node.table} VALUES ({values})"

    # UPDATE statement
    if isinstance(node, Update):
        return (
            f"UPDATE {node.table} "
            f"SET {node.col_set} = {node.val_set} "
            f"WHERE {node.cond_col} = {node.cond_val}"
        )

    # DELETE statement
    if isinstance(node, Delete):
        return f"DELETE FROM {node.table} WHERE {node.column} {node.op} {node.value}"

    # DROP COLUMN (ALTER TABLE)
    if isinstance(node, DropColumn):
        drop_parts = ", ".join([f"DROP COLUMN {col}" for col in node.columns])
        return f"ALTER TABLE {node.table} {drop_parts}"

    return f"-- Unknown AST node: {type(node).__name__}"


def generate_where(where_node):
    """Generate WHERE clause from Where AST node."""
    if not where_node or not where_node.left:
        return ""

    return "WHERE " + generate_condition(where_node.left)


def generate_condition(node):
    """Generate condition expression from AST node."""
    if node is None:
        return ""

    # Simple condition: column op value
    if isinstance(node, Condition):
        return f"{node.column} {node.op} {node.value}"

    # AND condition
    if isinstance(node, And):
        left = generate_condition(node.left)
        right = generate_condition(node.right)
        return f"({left} AND {right})"

    # OR condition
    if isinstance(node, Or):
        left = generate_condition(node.left)
        right = generate_condition(node.right)
        return f"({left} OR {right})"

    # BETWEEN condition
    if isinstance(node, Between):
        return f"{node.column} BETWEEN {node.low} AND {node.high}"

    # IN condition
    if isinstance(node, In):
        values = ", ".join(str(v) for v in node.values)
        return f"{node.column} IN ({values})"

    # LIKE condition
    if isinstance(node, Like):
        return f"{node.column} LIKE '{node.pattern}'"

    return str(node)


# =========================================================
#                   MAIN PIPELINE
# =========================================================

def parse_natural_language(text, use_new_pipeline=True):
    """
    Complete pipeline: Natural Language → SQL
    
    Args:
        text: Natural language query
        use_new_pipeline: If True, use Lexer→Parser→SQL. If False, use legacy regex.
    
    Returns a dictionary with all intermediate results.
    """
    # Try new pipeline first (Lexer → Parser → AST → SQL)
    if use_new_pipeline and HAS_NEW_PIPELINE:
        try:
            pipeline = NLToSQLPipeline()
            result = pipeline.process(text)
            return {
                "input": text,
                "method": "Lexer → Parser → AST → SQL",
                "tokens": result["tokens"],
                "ast": result["ast"],
                "sql": result["sql"],
                "explanation": f"Successfully parsed using Lexer-Parser pipeline"
            }
        except Exception as e:
            # Fall back to legacy method if new pipeline fails
            pass
    
    # Fallback: Legacy method (English → DSL → AST → SQL)
    # Step 1: English → DSL
    dsl = english_to_dsl(text)
    
    # Step 2: DSL → AST
    ast = parse_dsl(dsl)
    
    # Step 3: AST → SQL
    sql = ast_to_sql(ast)
    
    # Build explanation
    if sql.startswith("--"):
        explanation = f"Could not parse: {text}"
    else:
        explanation = f"Converted natural language to SQL (legacy regex method)"
    
    return {
        "input": text,
        "method": "English → DSL → AST → SQL (regex)",
        "dsl": dsl,
        "ast": ast_to_dict(ast),
        "sql": sql,
        "explanation": explanation
    }


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No input provided", "sql": "", "explanation": "Please provide a query"}))
        return

    text = " ".join(sys.argv[1:])
    
    # Parse with new pipeline (fallback to legacy if needed)
    result = parse_natural_language(text, use_new_pipeline=True)
    
    # Output JSON for API consumption
    output = {
        "sql": result["sql"],
        "explanation": result["explanation"],
        "method": result.get("method", "unknown")
    }
    
    # Add tokens if available (new pipeline)
    if "tokens" in result:
        output["tokens"] = result["tokens"]
    
    # Add AST
    output["ast"] = result.get("ast", {})
    
    # Add DSL if available (legacy method)
    if "dsl" in result:
        output["dsl"] = result["dsl"]
    
    print(json.dumps(output))


if __name__ == "__main__":
    main()
