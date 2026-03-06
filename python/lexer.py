"""
LEXICAL ANALYSIS (Lexer)
Tokenize natural language input into tokens.

This module implements the first stage of the parsing pipeline:
Input Text → Tokens (Keywords, Identifiers, Operators, Literals)
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token types for the lexer."""
    # Keywords - Commands
    SELECT = auto()
    SHOW = auto()
    LIST = auto()
    GET = auto()
    FIND = auto()
    COUNT = auto()
    SUM = auto()
    INSERT = auto()
    UPDATE = auto()
    DELETE = auto()
    
    # Keywords - Clauses
    FROM = auto()
    WHERE = auto()
    AND = auto()
    OR = auto()
    ORDER = auto()
    BY = auto()
    GROUP = auto()
    INTO = auto()
    SET = auto()
    VALUES = auto()
    
    # Keywords - Modifiers
    ALL = auto()
    DISTINCT = auto()
    UNIQUE = auto()
    ASC = auto()
    DESC = auto()
    
    # Keywords - Conditions
    BETWEEN = auto()
    IN = auto()
    LIKE = auto()
    CONTAINS = auto()
    
    # Keywords - Aggregates
    HOW = auto()
    MANY = auto()
    TOTAL = auto()
    
    # Keywords - Table operations
    ALTER = auto()
    TABLE = auto()
    DROP = auto()
    COLUMN = auto()
    
    # Operators
    EQUALS = auto()         # =
    NOT_EQUALS = auto()     # !=
    GREATER = auto()        # >
    LESS = auto()           # <
    GREATER_EQ = auto()     # >=
    LESS_EQ = auto()        # <=
    
    # Literals
    NUMBER = auto()         # 123, 45.67
    STRING = auto()         # 'hello', "world"
    IDENTIFIER = auto()     # table_name, column_name
    
    # Punctuation
    COMMA = auto()          # ,
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    STAR = auto()           # *
    
    # Special
    EOF = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    """Represents a single token."""
    type: TokenType
    value: str
    position: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', pos={self.position})"


class Lexer:
    """
    Lexical Analyzer - Tokenizes natural language input.
    
    Converts input text into a stream of tokens that can be
    processed by the parser.
    """
    
    # Keyword mappings (case-insensitive)
    KEYWORDS = {
        # Commands
        'select': TokenType.SELECT,
        'show': TokenType.SELECT,      # Alias for SELECT
        'list': TokenType.SELECT,      # Alias for SELECT
        'get': TokenType.SELECT,       # Alias for SELECT
        'find': TokenType.FIND,
        'count': TokenType.COUNT,
        'sum': TokenType.SUM,
        'insert': TokenType.INSERT,
        'update': TokenType.UPDATE,
        'delete': TokenType.DELETE,
        'remove': TokenType.DELETE,    # Alias for DELETE
        
        # Clauses
        'from': TokenType.FROM,
        'of': TokenType.FROM,          # Alias for FROM
        'where': TokenType.WHERE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'order': TokenType.ORDER,
        'by': TokenType.BY,
        'group': TokenType.GROUP,
        'into': TokenType.INTO,
        'set': TokenType.SET,
        'values': TokenType.VALUES,
        
        # Modifiers
        'all': TokenType.ALL,
        'distinct': TokenType.DISTINCT,
        'unique': TokenType.DISTINCT,  # Alias for DISTINCT
        'asc': TokenType.ASC,
        'ascending': TokenType.ASC,
        'desc': TokenType.DESC,
        'descending': TokenType.DESC,
        
        # Conditions
        'between': TokenType.BETWEEN,
        'in': TokenType.IN,
        'like': TokenType.LIKE,
        'contains': TokenType.CONTAINS,
        
        # Aggregates
        'how': TokenType.HOW,
        'many': TokenType.MANY,
        'total': TokenType.TOTAL,
        
        # Table operations
        'alter': TokenType.ALTER,
        'table': TokenType.TABLE,
        'drop': TokenType.DROP,
        'column': TokenType.COLUMN,
        'columns': TokenType.COLUMN,
        'col': TokenType.COLUMN,
    }
    
    # Natural language operator mappings
    OPERATOR_PHRASES = [
        ('greater than or equal to', '>='),
        ('less than or equal to', '<='),
        ('greater than', '>'),
        ('more than', '>'),
        ('less than', '<'),
        ('is equal to', '='),
        ('equal to', '='),
        ('equals', '='),
        ('equal', '='),
        ('same as', '='),
        ('not equal to', '!='),
        ('not equal', '!='),
        ('different from', '!='),
    ]
    
    def __init__(self, text: str):
        self.original_text = text
        self.text = self._preprocess(text)
        self.pos = 0
        self.tokens: List[Token] = []
        
    def _preprocess(self, text: str) -> str:
        """Preprocess text: normalize operators and clean up."""
        t = text.lower().strip()
        
        # Replace natural language operators with symbols
        for phrase, symbol in self.OPERATOR_PHRASES:
            t = t.replace(phrase, f' {symbol} ')
        
        # Normalize whitespace
        t = re.sub(r'\s+', ' ', t)
        
        return t
    
    def _current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]
    
    def _peek(self, offset: int = 1) -> Optional[str]:
        """Peek at character at offset from current position."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]
    
    def _advance(self) -> str:
        """Advance position and return current character."""
        char = self._current_char()
        self.pos += 1
        return char
    
    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self._current_char() and self._current_char().isspace():
            self._advance()
    
    def _read_number(self) -> Token:
        """Read a number token (integer or float)."""
        start_pos = self.pos
        result = ''
        
        while self._current_char() and (self._current_char().isdigit() or self._current_char() == '.'):
            result += self._advance()
        
        return Token(TokenType.NUMBER, result, start_pos)
    
    def _read_string(self) -> Token:
        """Read a quoted string token."""
        start_pos = self.pos
        quote_char = self._advance()  # Consume opening quote
        result = ''
        
        while self._current_char() and self._current_char() != quote_char:
            result += self._advance()
        
        if self._current_char() == quote_char:
            self._advance()  # Consume closing quote
        
        return Token(TokenType.STRING, result, start_pos)
    
    def _read_word(self) -> Token:
        """Read a word (keyword or identifier)."""
        start_pos = self.pos
        result = ''
        
        while self._current_char() and (self._current_char().isalnum() or self._current_char() == '_'):
            result += self._advance()
        
        # Check if it's a keyword
        lower_result = result.lower()
        if lower_result in self.KEYWORDS:
            return Token(self.KEYWORDS[lower_result], result, start_pos)
        
        return Token(TokenType.IDENTIFIER, result, start_pos)
    
    def _read_operator(self) -> Token:
        """Read an operator token."""
        start_pos = self.pos
        char = self._current_char()
        next_char = self._peek()
        
        # Two-character operators
        if char == '>' and next_char == '=':
            self._advance()
            self._advance()
            return Token(TokenType.GREATER_EQ, '>=', start_pos)
        if char == '<' and next_char == '=':
            self._advance()
            self._advance()
            return Token(TokenType.LESS_EQ, '<=', start_pos)
        if char == '!' and next_char == '=':
            self._advance()
            self._advance()
            return Token(TokenType.NOT_EQUALS, '!=', start_pos)
        
        # Single-character operators
        operators = {
            '=': TokenType.EQUALS,
            '>': TokenType.GREATER,
            '<': TokenType.LESS,
            ',': TokenType.COMMA,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '*': TokenType.STAR,
        }
        
        if char in operators:
            self._advance()
            return Token(operators[char], char, start_pos)
        
        # Unknown character
        self._advance()
        return Token(TokenType.UNKNOWN, char, start_pos)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the input text and return list of tokens."""
        self.tokens = []
        
        while self.pos < len(self.text):
            self._skip_whitespace()
            
            if self.pos >= len(self.text):
                break
            
            char = self._current_char()
            
            # Number
            if char.isdigit():
                self.tokens.append(self._read_number())
            # String
            elif char in '"\'':
                self.tokens.append(self._read_string())
            # Word (keyword or identifier)
            elif char.isalpha() or char == '_':
                self.tokens.append(self._read_word())
            # Operator or punctuation
            else:
                token = self._read_operator()
                if token.type != TokenType.UNKNOWN:
                    self.tokens.append(token)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.pos))
        
        return self.tokens
    
    def get_tokens_summary(self) -> dict:
        """Get a summary of tokens for debugging."""
        return {
            'original': self.original_text,
            'preprocessed': self.text,
            'token_count': len(self.tokens),
            'tokens': [
                {'type': t.type.name, 'value': t.value, 'pos': t.position}
                for t in self.tokens
            ]
        }


def tokenize(text: str) -> List[Token]:
    """Convenience function to tokenize text."""
    lexer = Lexer(text)
    return lexer.tokenize()


# =========================================================
#                   TEST LEXER
# =========================================================

def test_lexer():
    """Test the lexer with sample inputs."""
    test_cases = [
        "select all from users",
        "show all products where price > 100",
        "count users where age greater than 20",
        "insert into users values 1, 'John', 25",
        "select distinct city from customers",
        "find users where name contains 'an'",
        "select users where age between 20 and 30",
    ]
    
    print("=" * 60)
    print("LEXER TEST")
    print("=" * 60)
    
    for text in test_cases:
        print(f"\nInput: {text}")
        lexer = Lexer(text)
        tokens = lexer.tokenize()
        print(f"Tokens: {len(tokens)}")
        for token in tokens:
            if token.type != TokenType.EOF:
                print(f"  {token}")
        print("-" * 40)


if __name__ == "__main__":
    test_lexer()
