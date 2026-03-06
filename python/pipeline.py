"""
Natural Language to SQL - Complete Pipeline
============================================

This module integrates all stages of the parsing pipeline:
1. LEXER: Input Text → Tokens
2. PARSER: Tokens → AST (Abstract Syntax Tree)  
3. SQL GENERATOR: AST → SQL Query

Architecture:
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Natural      │────▶│    LEXER     │────▶│    PARSER    │────▶│     SQL      │
    │ Language     │     │  (Tokenize)  │     │   (AST)      │     │  Generator   │
    └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
"""

import json
from typing import Any, Dict, List, Optional

# Import from our modules
from lexer import Lexer, Token, TokenType, tokenize
from syntax_parser import (
    Parser, ASTNode, SelectNode, InsertNode, UpdateNode, DeleteNode,
    AlterTableNode, WhereNode, SimpleCondition, AndCondition, OrCondition,
    BetweenCondition, InCondition, LikeCondition, OrderByNode, GroupByNode,
    AggregateNode, ast_to_dict, parse as parse_to_ast
)


# =========================================================
#                   AST → SQL GENERATOR
# =========================================================

def format_value(value: Any) -> str:
    """Format a value for SQL."""
    if isinstance(value, str):
        # Check if it's already a number string
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return value
        # Check for float
        try:
            float(value)
            return value
        except ValueError:
            pass
        # String literal
        return f"'{value}'"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        return f"'{value}'"


def condition_to_sql(condition: Any) -> str:
    """Convert condition node to SQL WHERE clause."""
    if condition is None:
        return ""
    
    if isinstance(condition, SimpleCondition):
        value = format_value(condition.value)
        return f"{condition.column} {condition.operator} {value}"
    
    if isinstance(condition, AndCondition):
        left = condition_to_sql(condition.left)
        right = condition_to_sql(condition.right)
        return f"{left} AND {right}"
    
    if isinstance(condition, OrCondition):
        left = condition_to_sql(condition.left)
        right = condition_to_sql(condition.right)
        return f"({left} OR {right})"
    
    if isinstance(condition, BetweenCondition):
        return f"{condition.column} BETWEEN {condition.low} AND {condition.high}"
    
    if isinstance(condition, InCondition):
        values = ', '.join(format_value(v) for v in condition.values)
        return f"{condition.column} IN ({values})"
    
    if isinstance(condition, LikeCondition):
        pattern = condition.pattern
        if '%' not in pattern:
            pattern = f'%{pattern}%'
        return f"{condition.column} LIKE '{pattern}'"
    
    return str(condition)


def ast_to_sql(ast: ASTNode) -> str:
    """
    Convert AST to SQL query.
    
    This is the final stage of the pipeline:
    AST → SQL Query String
    """
    if isinstance(ast, SelectNode):
        # Build SELECT clause
        columns = ', '.join(ast.columns)
        sql = f"SELECT {'DISTINCT ' if ast.distinct else ''}{columns} FROM {ast.table}"
        
        # Add WHERE clause
        if ast.where:
            where_sql = condition_to_sql(ast.where.condition)
            sql += f" WHERE {where_sql}"
        
        # Add ORDER BY
        if ast.order_by:
            sql += f" ORDER BY {ast.order_by.column} {ast.order_by.direction}"
        
        # Add GROUP BY
        if ast.group_by:
            sql += f" GROUP BY {ast.group_by.column}"
        
        return sql + ";"
    
    if isinstance(ast, InsertNode):
        values = ', '.join(format_value(v) for v in ast.values)
        return f"INSERT INTO {ast.table} VALUES ({values});"
    
    if isinstance(ast, UpdateNode):
        value = format_value(ast.set_value)
        sql = f"UPDATE {ast.table} SET {ast.set_column} = {value}"
        
        if ast.where:
            where_sql = condition_to_sql(ast.where.condition)
            sql += f" WHERE {where_sql}"
        
        return sql + ";"
    
    if isinstance(ast, DeleteNode):
        sql = f"DELETE FROM {ast.table}"
        
        if ast.where:
            where_sql = condition_to_sql(ast.where.condition)
            sql += f" WHERE {where_sql}"
        
        return sql + ";"
    
    if isinstance(ast, AlterTableNode):
        if ast.action == 'DROP COLUMN':
            columns = ', '.join(ast.columns)
            return f"ALTER TABLE {ast.table} DROP COLUMN {columns};"
        return f"ALTER TABLE {ast.table} {ast.action};"
    
    raise ValueError(f"Unknown AST node type: {type(ast).__name__}")


# =========================================================
#                   COMPLETE PIPELINE
# =========================================================

class NLToSQLPipeline:
    """
    Complete Natural Language to SQL Pipeline.
    
    Stages:
    1. Lexer: Tokenize input text
    2. Parser: Build AST from tokens
    3. SQL Generator: Convert AST to SQL
    """
    
    def __init__(self):
        self.last_tokens = None
        self.last_ast = None
        self.last_sql = None
        
    def tokenize(self, text: str) -> List[Token]:
        """Stage 1: Lexical Analysis - Tokenize input."""
        lexer = Lexer(text)
        self.last_tokens = lexer.tokenize()
        return self.last_tokens
    
    def parse(self, tokens: List[Token] = None, text: str = None) -> ASTNode:
        """Stage 2: Syntax Analysis - Parse tokens to AST."""
        if text and not tokens:
            tokens = self.tokenize(text)
        elif tokens is None:
            tokens = self.last_tokens
        
        parser = Parser(tokens)
        self.last_ast = parser.parse()
        return self.last_ast
    
    def generate_sql(self, ast: ASTNode = None) -> str:
        """Stage 3: Code Generation - Convert AST to SQL."""
        if ast is None:
            ast = self.last_ast
        
        self.last_sql = ast_to_sql(ast)
        return self.last_sql
    
    def process(self, text: str) -> Dict[str, Any]:
        """
        Complete pipeline: Natural Language → SQL.
        
        Returns a dictionary with all intermediate results.
        """
        # Stage 1: Lexer
        tokens = self.tokenize(text)
        
        # Stage 2: Parser
        ast = self.parse(tokens)
        
        # Stage 3: SQL Generator
        sql = self.generate_sql(ast)
        
        return {
            'input': text,
            'tokens': [{'type': t.type.name, 'value': t.value} for t in tokens if t.type != TokenType.EOF],
            'ast': ast_to_dict(ast),
            'sql': sql
        }
    
    def quick_parse(self, text: str) -> str:
        """Quick parse: Natural Language → SQL (just returns SQL)."""
        result = self.process(text)
        return result['sql']


# =========================================================
#                   CONVENIENCE FUNCTIONS
# =========================================================

def nl_to_sql(text: str) -> str:
    """Convert natural language to SQL."""
    pipeline = NLToSQLPipeline()
    return pipeline.quick_parse(text)


def process_text(text: str) -> Dict[str, Any]:
    """Process natural language and return full pipeline results."""
    pipeline = NLToSQLPipeline()
    return pipeline.process(text)


# =========================================================
#                   TEST PIPELINE
# =========================================================

def test_pipeline():
    """Test the complete pipeline with sample inputs."""
    test_cases = [
        # SELECT queries
        "select all from users",
        "show all products from inventory",
        "select distinct city from customers",
        "show all products where price > 100",
        "select users where age greater than 20 and salary less than 5000",
        "select products where price between 10 and 100",
        "select all products order by price desc",
        
        # COUNT queries
        "count users",
        "how many products",
        
        # INSERT queries
        "insert into users values 1, 'John', 25",
        
        # UPDATE queries
        "update users set age = 25 where id = 10",
        
        # DELETE queries
        "delete from users where id = 5",
        
        # LIKE/CONTAINS queries
        "find users where name contains 'an'",
        
        # ALTER queries
        "delete column age from users",
        "alter table users drop column age",
    ]
    
    print("=" * 70)
    print("COMPLETE PIPELINE TEST: Natural Language → Lexer → Parser → SQL")
    print("=" * 70)
    
    pipeline = NLToSQLPipeline()
    passed = 0
    failed = 0
    
    for text in test_cases:
        print(f"\n📝 Input: {text}")
        try:
            result = pipeline.process(text)
            
            print(f"   🔤 Tokens: {len(result['tokens'])}")
            print(f"   🌳 AST Type: {result['ast']['type']}")
            print(f"   ✅ SQL: {result['sql']}")
            passed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
        print("-" * 50)
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed, {len(test_cases)} total")
    print("=" * 70)


if __name__ == "__main__":
    test_pipeline()
