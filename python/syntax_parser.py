"""
SYNTAX ANALYSIS (Parser)
Parse tokens into Abstract Syntax Tree (AST).

This module implements the second stage of the parsing pipeline:
Tokens → Parse Tree → AST

Uses recursive descent parsing with grammar rules for SQL-like queries.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Any
from enum import Enum, auto

from lexer import Token, TokenType, Lexer, tokenize


# =========================================================
#                   AST NODE CLASSES
# =========================================================

class ASTNode:
    """Base class for all AST nodes."""
    pass


@dataclass
class SelectNode(ASTNode):
    """SELECT statement AST node."""
    columns: List[str]
    table: str
    where: Optional['WhereNode'] = None
    order_by: Optional['OrderByNode'] = None
    group_by: Optional['GroupByNode'] = None
    distinct: bool = False
    aggregate: Optional['AggregateNode'] = None


@dataclass
class WhereNode(ASTNode):
    """WHERE clause AST node."""
    condition: 'ConditionNode'


@dataclass
class ConditionNode(ASTNode):
    """Base condition node."""
    pass


@dataclass
class SimpleCondition(ConditionNode):
    """Simple condition: column op value."""
    column: str
    operator: str
    value: Any


@dataclass
class AndCondition(ConditionNode):
    """AND condition: left AND right."""
    left: ConditionNode
    right: ConditionNode


@dataclass
class OrCondition(ConditionNode):
    """OR condition: left OR right."""
    left: ConditionNode
    right: ConditionNode


@dataclass
class BetweenCondition(ConditionNode):
    """BETWEEN condition: column BETWEEN low AND high."""
    column: str
    low: Any
    high: Any


@dataclass
class InCondition(ConditionNode):
    """IN condition: column IN (values)."""
    column: str
    values: List[Any]


@dataclass
class LikeCondition(ConditionNode):
    """LIKE condition: column LIKE pattern."""
    column: str
    pattern: str


@dataclass
class OrderByNode(ASTNode):
    """ORDER BY clause AST node."""
    column: str
    direction: str = "ASC"


@dataclass
class GroupByNode(ASTNode):
    """GROUP BY clause AST node."""
    column: str


@dataclass
class AggregateNode(ASTNode):
    """Aggregate function node (COUNT, SUM, etc.)."""
    function: str
    column: Optional[str] = None


@dataclass
class InsertNode(ASTNode):
    """INSERT statement AST node."""
    table: str
    values: List[Any]
    columns: Optional[List[str]] = None


@dataclass
class UpdateNode(ASTNode):
    """UPDATE statement AST node."""
    table: str
    set_column: str
    set_value: Any
    where: Optional[WhereNode] = None


@dataclass
class DeleteNode(ASTNode):
    """DELETE statement AST node."""
    table: str
    where: Optional[WhereNode] = None


@dataclass
class AlterTableNode(ASTNode):
    """ALTER TABLE statement AST node."""
    table: str
    action: str  # DROP COLUMN, ADD COLUMN, etc.
    columns: List[str]


# =========================================================
#                   PARSER CLASS
# =========================================================

class ParseError(Exception):
    """Parser error exception."""
    pass


class Parser:
    """
    Syntax Analyzer - Parses tokens into AST.
    
    Uses recursive descent parsing to build an Abstract Syntax Tree
    from the token stream.
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def _current_token(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def _peek(self, offset: int = 1) -> Token:
        """Peek at token at offset from current position."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def _advance(self) -> Token:
        """Advance to next token and return current."""
        token = self._current_token()
        self.pos += 1
        return token
    
    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self._current_token().type in types
    
    def _expect(self, token_type: TokenType) -> Token:
        """Expect current token to be of given type, advance and return it."""
        if not self._match(token_type):
            raise ParseError(f"Expected {token_type.name}, got {self._current_token().type.name}")
        return self._advance()
    
    def _consume_if(self, token_type: TokenType) -> Optional[Token]:
        """Consume token if it matches, otherwise return None."""
        if self._match(token_type):
            return self._advance()
        return None
    
    def parse(self) -> ASTNode:
        """Parse tokens and return AST root node."""
        token = self._current_token()
        
        # SELECT / SHOW / LIST / GET
        if self._match(TokenType.SELECT):
            return self._parse_select()
        
        # COUNT / HOW MANY
        if self._match(TokenType.COUNT) or self._match(TokenType.HOW):
            return self._parse_count()
        
        # SUM / TOTAL
        if self._match(TokenType.SUM, TokenType.TOTAL):
            return self._parse_sum()
        
        # FIND (with LIKE/CONTAINS)
        if self._match(TokenType.FIND):
            return self._parse_find()
        
        # INSERT
        if self._match(TokenType.INSERT):
            return self._parse_insert()
        
        # UPDATE
        if self._match(TokenType.UPDATE):
            return self._parse_update()
        
        # DELETE
        if self._match(TokenType.DELETE):
            return self._parse_delete()
        
        # ALTER TABLE
        if self._match(TokenType.ALTER):
            return self._parse_alter()
        
        raise ParseError(f"Unexpected token: {token.type.name} '{token.value}'")
    
    def _parse_select(self) -> SelectNode:
        """Parse SELECT statement.
        
        Handles various forms:
        - "select all from users"
        - "select * from users"
        - "select name, age from users"
        - "select users where..." (table as first identifier)
        """
        self._advance()  # Consume SELECT
        
        distinct = False
        columns = []
        table = None
        
        # Check for DISTINCT
        if self._match(TokenType.DISTINCT):
            self._advance()
            distinct = True
        
        # Check for ALL
        if self._match(TokenType.ALL):
            self._advance()
            columns = ['*']
            # Parse FROM clause
            table = self._parse_from(allow_missing=False)
        elif self._match(TokenType.STAR):
            self._advance()
            columns = ['*']
            # Parse FROM clause
            table = self._parse_from(allow_missing=False)
        else:
            # Could be:
            # 1. "select name, age from users" (column list + FROM)
            # 2. "select users where..." (table name + WHERE)
            
            first_identifier = None
            if self._match(TokenType.IDENTIFIER):
                first_identifier = self._advance().value
            
            # Check what comes next
            if self._match(TokenType.COMMA):
                # It's a column list: "select name, age from users"
                columns = [first_identifier]
                while self._match(TokenType.COMMA):
                    self._advance()
                    if self._match(TokenType.IDENTIFIER):
                        columns.append(self._advance().value)
                table = self._parse_from(allow_missing=False)
            elif self._match(TokenType.FROM):
                # It's "select column from table"
                columns = [first_identifier]
                table = self._parse_from(allow_missing=False)
            elif self._match(TokenType.WHERE, TokenType.ORDER, TokenType.GROUP, TokenType.EOF):
                # It's "select table where..." (table is first identifier)
                # This is shorthand for "select * from table where..."
                columns = ['*']
                table = first_identifier
            else:
                # Default: treat as columns and look for FROM
                columns = [first_identifier] if first_identifier else ['*']
                table = self._parse_from(allow_missing=True)
                if table is None:
                    table = first_identifier
                    columns = ['*']
        
        # Parse optional WHERE
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        # Parse optional ORDER BY
        order_by = None
        if self._match(TokenType.ORDER):
            order_by = self._parse_order_by()
        
        # Parse optional GROUP BY
        group_by = None
        if self._match(TokenType.GROUP):
            group_by = self._parse_group_by()
        
        return SelectNode(
            columns=columns,
            table=table,
            where=where,
            order_by=order_by,
            group_by=group_by,
            distinct=distinct
        )
    
    def _parse_column_list(self) -> List[str]:
        """Parse list of column names."""
        columns = []
        
        if self._match(TokenType.IDENTIFIER):
            columns.append(self._advance().value)
            
            while self._match(TokenType.COMMA):
                self._advance()  # Consume comma
                if self._match(TokenType.IDENTIFIER):
                    columns.append(self._advance().value)
        
        return columns if columns else ['*']
    
    def _parse_from(self, allow_missing: bool = False) -> str:
        """Parse FROM clause and return table name.
        
        Args:
            allow_missing: If True, don't require FROM keyword.
                          This handles cases like "select users where..."
        """
        if self._match(TokenType.FROM):
            self._advance()  # Consume FROM
        elif not allow_missing:
            # Check if next token is an identifier (table name without FROM)
            if not self._match(TokenType.IDENTIFIER):
                raise ParseError("Expected table name after FROM")
        
        if self._match(TokenType.IDENTIFIER):
            return self._advance().value
        
        # If we get here and allow_missing is False, it's an error
        if not allow_missing:
            raise ParseError("Expected table name after FROM")
        
        return None
    
    def _parse_where(self) -> WhereNode:
        """Parse WHERE clause."""
        self._advance()  # Consume WHERE
        condition = self._parse_condition()
        return WhereNode(condition)
    
    def _parse_condition(self) -> ConditionNode:
        """Parse condition expression."""
        left = self._parse_simple_condition()
        
        # Check for AND/OR
        while self._match(TokenType.AND, TokenType.OR):
            op = self._advance()
            right = self._parse_simple_condition()
            
            if op.type == TokenType.AND:
                left = AndCondition(left, right)
            else:
                left = OrCondition(left, right)
        
        return left
    
    def _parse_simple_condition(self) -> ConditionNode:
        """Parse simple condition."""
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected column name in condition")
        
        column = self._advance().value
        
        # Check for BETWEEN
        if self._match(TokenType.BETWEEN):
            self._advance()
            low = self._parse_value()
            self._expect(TokenType.AND)
            high = self._parse_value()
            return BetweenCondition(column, low, high)
        
        # Check for IN
        if self._match(TokenType.IN):
            self._advance()
            values = self._parse_value_list()
            return InCondition(column, values)
        
        # Check for LIKE/CONTAINS
        if self._match(TokenType.LIKE, TokenType.CONTAINS):
            self._advance()
            pattern = self._parse_value()
            return LikeCondition(column, str(pattern))
        
        # Simple comparison
        op = self._parse_operator()
        value = self._parse_value()
        
        return SimpleCondition(column, op, value)
    
    def _parse_operator(self) -> str:
        """Parse comparison operator."""
        op_map = {
            TokenType.EQUALS: '=',
            TokenType.NOT_EQUALS: '!=',
            TokenType.GREATER: '>',
            TokenType.LESS: '<',
            TokenType.GREATER_EQ: '>=',
            TokenType.LESS_EQ: '<=',
        }
        
        token = self._current_token()
        if token.type in op_map:
            self._advance()
            return op_map[token.type]
        
        raise ParseError(f"Expected operator, got {token.type.name}")
    
    def _parse_value(self) -> Any:
        """Parse a value (number, string, or identifier)."""
        token = self._current_token()
        
        if token.type == TokenType.NUMBER:
            self._advance()
            # Return as int or float
            if '.' in token.value:
                return float(token.value)
            return int(token.value)
        
        if token.type == TokenType.STRING:
            self._advance()
            return token.value
        
        if token.type == TokenType.IDENTIFIER:
            self._advance()
            return token.value
        
        raise ParseError(f"Expected value, got {token.type.name}")
    
    def _parse_value_list(self) -> List[Any]:
        """Parse list of values."""
        values = []
        
        # Optional opening paren
        has_paren = self._consume_if(TokenType.LPAREN)
        
        values.append(self._parse_value())
        
        while self._match(TokenType.COMMA):
            self._advance()
            values.append(self._parse_value())
        
        if has_paren:
            self._consume_if(TokenType.RPAREN)
        
        return values
    
    def _parse_order_by(self) -> OrderByNode:
        """Parse ORDER BY clause."""
        self._advance()  # Consume ORDER
        self._expect(TokenType.BY)
        
        if not self._match(TokenType.IDENTIFIER):
            # Default to 'id' if no column specified
            column = 'id'
        else:
            column = self._advance().value
        
        direction = "ASC"
        if self._match(TokenType.ASC):
            self._advance()
            direction = "ASC"
        elif self._match(TokenType.DESC):
            self._advance()
            direction = "DESC"
        
        return OrderByNode(column, direction)
    
    def _parse_group_by(self) -> GroupByNode:
        """Parse GROUP BY clause."""
        self._advance()  # Consume GROUP
        self._expect(TokenType.BY)
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected column name after GROUP BY")
        
        column = self._advance().value
        return GroupByNode(column)
    
    def _parse_count(self) -> SelectNode:
        """Parse COUNT query."""
        self._advance()  # Consume COUNT or HOW
        
        # Handle "HOW MANY"
        if self._match(TokenType.MANY):
            self._advance()
        
        # Get what to count (table or column)
        target = None
        if self._match(TokenType.IDENTIFIER):
            target = self._advance().value
        
        # Check for FROM
        table = target
        if self._match(TokenType.FROM):
            self._advance()
            if self._match(TokenType.IDENTIFIER):
                table = self._advance().value
        
        # Parse optional WHERE
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        return SelectNode(
            columns=['COUNT(*)'],
            table=table,
            where=where,
            aggregate=AggregateNode('COUNT', None)
        )
    
    def _parse_sum(self) -> SelectNode:
        """Parse SUM query."""
        self._advance()  # Consume SUM/TOTAL
        
        column = None
        if self._match(TokenType.IDENTIFIER):
            column = self._advance().value
        
        table = column
        if self._match(TokenType.FROM):
            self._advance()
            if self._match(TokenType.IDENTIFIER):
                table = self._advance().value
        
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        return SelectNode(
            columns=[f'SUM({column})' if column else 'SUM(*)'],
            table=table,
            where=where,
            aggregate=AggregateNode('SUM', column)
        )
    
    def _parse_find(self) -> SelectNode:
        """Parse FIND query (usually with LIKE/CONTAINS)."""
        self._advance()  # Consume FIND
        
        # Get table name
        table = None
        if self._match(TokenType.IDENTIFIER):
            table = self._advance().value
        
        # Parse WHERE
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        return SelectNode(
            columns=['*'],
            table=table,
            where=where
        )
    
    def _parse_insert(self) -> InsertNode:
        """Parse INSERT statement."""
        self._advance()  # Consume INSERT
        self._expect(TokenType.INTO)
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected table name after INSERT INTO")
        table = self._advance().value
        
        self._expect(TokenType.VALUES)
        
        values = self._parse_value_list()
        
        return InsertNode(table=table, values=values)
    
    def _parse_update(self) -> UpdateNode:
        """Parse UPDATE statement."""
        self._advance()  # Consume UPDATE
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected table name after UPDATE")
        table = self._advance().value
        
        self._expect(TokenType.SET)
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected column name after SET")
        set_column = self._advance().value
        
        self._expect(TokenType.EQUALS)
        set_value = self._parse_value()
        
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        return UpdateNode(table=table, set_column=set_column, set_value=set_value, where=where)
    
    def _parse_delete(self) -> DeleteNode:
        """Parse DELETE statement."""
        self._advance()  # Consume DELETE
        
        # Check for "DELETE COLUMN" (ALTER TABLE)
        if self._match(TokenType.COLUMN):
            return self._parse_drop_column()
        
        # DELETE FROM table
        if self._match(TokenType.FROM):
            self._advance()
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected table name after DELETE FROM")
        table = self._advance().value
        
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_where()
        
        return DeleteNode(table=table, where=where)
    
    def _parse_drop_column(self) -> AlterTableNode:
        """Parse DROP COLUMN (via DELETE COLUMN)."""
        self._advance()  # Consume COLUMN
        
        columns = []
        if self._match(TokenType.IDENTIFIER):
            columns.append(self._advance().value)
            
            while self._match(TokenType.COMMA):
                self._advance()
                if self._match(TokenType.IDENTIFIER):
                    columns.append(self._advance().value)
        
        # FROM table
        self._expect(TokenType.FROM)
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected table name after FROM")
        table = self._advance().value
        
        return AlterTableNode(table=table, action='DROP COLUMN', columns=columns)
    
    def _parse_alter(self) -> AlterTableNode:
        """Parse ALTER TABLE statement."""
        self._advance()  # Consume ALTER
        self._expect(TokenType.TABLE)
        
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError("Expected table name after ALTER TABLE")
        table = self._advance().value
        
        self._expect(TokenType.DROP)
        self._expect(TokenType.COLUMN)
        
        columns = []
        if self._match(TokenType.IDENTIFIER):
            columns.append(self._advance().value)
        
        return AlterTableNode(table=table, action='DROP COLUMN', columns=columns)


def parse(text: str) -> ASTNode:
    """Convenience function to parse text into AST."""
    tokens = tokenize(text)
    parser = Parser(tokens)
    return parser.parse()


# =========================================================
#                   AST TO DICT
# =========================================================

def ast_to_dict(node: ASTNode) -> dict:
    """Convert AST node to dictionary for serialization."""
    if node is None:
        return None
    
    if isinstance(node, SelectNode):
        return {
            'type': 'SELECT',
            'columns': node.columns,
            'table': node.table,
            'distinct': node.distinct,
            'where': ast_to_dict(node.where),
            'order_by': ast_to_dict(node.order_by),
            'group_by': ast_to_dict(node.group_by),
            'aggregate': ast_to_dict(node.aggregate)
        }
    
    if isinstance(node, WhereNode):
        return {
            'type': 'WHERE',
            'condition': ast_to_dict(node.condition)
        }
    
    if isinstance(node, SimpleCondition):
        return {
            'type': 'CONDITION',
            'column': node.column,
            'operator': node.operator,
            'value': node.value
        }
    
    if isinstance(node, AndCondition):
        return {
            'type': 'AND',
            'left': ast_to_dict(node.left),
            'right': ast_to_dict(node.right)
        }
    
    if isinstance(node, OrCondition):
        return {
            'type': 'OR',
            'left': ast_to_dict(node.left),
            'right': ast_to_dict(node.right)
        }
    
    if isinstance(node, BetweenCondition):
        return {
            'type': 'BETWEEN',
            'column': node.column,
            'low': node.low,
            'high': node.high
        }
    
    if isinstance(node, InCondition):
        return {
            'type': 'IN',
            'column': node.column,
            'values': node.values
        }
    
    if isinstance(node, LikeCondition):
        return {
            'type': 'LIKE',
            'column': node.column,
            'pattern': node.pattern
        }
    
    if isinstance(node, OrderByNode):
        return {
            'type': 'ORDER_BY',
            'column': node.column,
            'direction': node.direction
        }
    
    if isinstance(node, GroupByNode):
        return {
            'type': 'GROUP_BY',
            'column': node.column
        }
    
    if isinstance(node, AggregateNode):
        return {
            'type': 'AGGREGATE',
            'function': node.function,
            'column': node.column
        }
    
    if isinstance(node, InsertNode):
        return {
            'type': 'INSERT',
            'table': node.table,
            'values': node.values,
            'columns': node.columns
        }
    
    if isinstance(node, UpdateNode):
        return {
            'type': 'UPDATE',
            'table': node.table,
            'set_column': node.set_column,
            'set_value': node.set_value,
            'where': ast_to_dict(node.where)
        }
    
    if isinstance(node, DeleteNode):
        return {
            'type': 'DELETE',
            'table': node.table,
            'where': ast_to_dict(node.where)
        }
    
    if isinstance(node, AlterTableNode):
        return {
            'type': 'ALTER_TABLE',
            'table': node.table,
            'action': node.action,
            'columns': node.columns
        }
    
    return str(node)


# =========================================================
#                   TEST PARSER
# =========================================================

def test_parser():
    """Test the parser with sample inputs."""
    test_cases = [
        "select all from users",
        "show all products where price > 100",
        "count users",
        "select users where age > 20 and salary < 5000",
        "insert into users values 1, 'John', 25",
        "update users set age = 25 where id = 10",
        "delete from users where id = 5",
        "select distinct city from customers",
        "select all products order by price desc",
        "find users where name contains 'an'",
        "select users where age between 20 and 30",
        "delete column age from users",
    ]
    
    print("=" * 60)
    print("PARSER TEST")
    print("=" * 60)
    
    import json
    
    for text in test_cases:
        print(f"\nInput: {text}")
        try:
            ast = parse(text)
            ast_dict = ast_to_dict(ast)
            print(f"AST: {json.dumps(ast_dict, indent=2)}")
        except ParseError as e:
            print(f"Parse Error: {e}")
        print("-" * 40)


if __name__ == "__main__":
    test_parser()
