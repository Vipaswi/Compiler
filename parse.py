import sys
from lex import *

# Parser object that keeps track of current token and checks if the code matches the grammer
class Parser:
  def __init__(self, lexer, emitter):
    self.lexer = lexer
    self.emitter = emitter

    self.symbols = set() # Variables declared so far
    self.labelsDeclared = set() # Labels declared so far
    self.labelsGotoed = set() # Labels that have goto'ed so far

    self.curToken = None
    self.peekToken = None
    self.nextToken()
    self.nextToken() # Called twice to initialize current and peek

  # Return True if the current token matches
  def checkToken(self, kind):
    return kind == self.curToken.kind

  # Returns true if the next token matches
  def checkPeek(self, kind):
    return kind == self.peekToken.kind

  # Try to match current token. If not, error. Advances the current token.
  def match(self, kind):
    if not self.checkToken(kind):
      self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
    self.nextToken()

  # Advances the current token.
  def nextToken(self):
    self.curToken = self.peekToken
    self.peekToken = self.lexer.getToken() #where it connects to the lexer to get the tokens.
    # EOF handles passing the EOF marker

  def abort(self, message):
    sys.exit("Error. " + message)

  # Production Rules

  # program ::= {statement} (program is equal to zero or more statements)
  def program(self):
    # Add the initial headers
    self.emitter.headerLine("#include <stdio.h>")
    self.emitter.headerLine("int main(void){")

    while self.checkToken(TokenType.NEWLINE): # Handles new lines at the beginning of the program
      self.nextToken()

    # Parse all the statements in the program
    while not self.checkToken(TokenType.EOF):
      self.statement()

    # Call the ends
    self.emitter.emitLine("return 0;")
    self.emitter.emitLine("}")
    
    for label in self.labelsGotoed:
      if label not in self.labelsDeclared:
        self.abort("Attempting to GOTO to an undeclared label: " + label)

  # One of the following statements...
  def statement(self):
    # Check the first token to see the type of statement it is

    # "Print" (expression | string)
    if self.checkToken(TokenType.PRINT):
      self.nextToken()

      if self.checkToken(TokenType.STRING):
        #It's a nice string
        self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
        self.nextToken()
      else:
        self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
        self.expression()
        self.emitter.emitLine("));")
    
    # "IF" comparison "THEN" {statement} "ENDIF"
    elif self.checkToken(TokenType.IF):
      self.nextToken()
      self.emitter.emit("if(")
      self.comparison() #Expression

      self.match(TokenType.THEN) # Required for TEENY TINY language following if
      self.nl()
      self.emitter.emitLine("){")

      #Zero or more statements allowed in the body:
      while not self.checkToken(TokenType.ENDIF):
        self.statement()
      
      self.match(TokenType.ENDIF)
      self.emitter.emitLine("}")

    #"WHILE" comparison "REPEAT" {statement} "ENDWHILE
    elif self.checkToken(TokenType.WHILE):
      self.nextToken()
      self.emitter.emit("while(")
      self.comparison() #Expression that returns a true false value

      self.match(TokenType.REPEAT) # Required for TEENY TINY language following if
      self.nl()
      self.emitter.emitLine("){")

      #Zero or more statements allowed in the body:
      while not self.checkToken(TokenType.ENDWHILE):
        self.statement()
      
      self.match(TokenType.ENDWHILE)
      self.emitter.emitLine("}")

    # "LABEL" ident
    elif self.checkToken(TokenType.LABEL):
      self.nextToken()

      # Make sure label is unique
      if self.curToken.text in self.labelsDeclared:
        self.abort("Label already exists: " + self.curToken.text)
      self.labelsDeclared.add(self.curToken.text)
      
      self.emitter.emitLine(self.curToken.text + ":")
      self.match(TokenType.IDENT)
    
    # "GOTO" ident
    elif self.checkToken(TokenType.GOTO):
      self.nextToken()
      self.labelsGotoed.add(self.curToken.text)
      self.emitter.emitLine("goto " + self.curToken.text +";")
      self.match(TokenType.IDENT)
    
    # "LET" ident "=" expression
    elif self.checkToken(TokenType.LET):
      self.nextToken()

      # Add identifier to set of symbols if not already done.
      if self.curToken.text not in self.symbols:
        self.symbols.add(self.curToken.text)
        self.emitter.headerLine("float " + self.curToken.text + ";")

      self.emitter.emit(self.curToken.text + " = ")
      self.match(TokenType.IDENT)
      self.match(TokenType.EQ)

      self.expression() #Evaluates an expression
      self.emitter.emitLine(";")
    
    # "INPUT" ident
    elif self.checkToken(TokenType.INPUT):
      self.nextToken()

      # If the variable doesn't exist, declare it:
      if self.curToken.text not in self.symbols:
        self.symbols.add(self.curToken.text)
        self.emitter.headerLine("float " + self.curToken.text + ";")
      
      # Emit scanf while validating the input; if it is invalid set the variable to 0 and clear input.
      self.emitter.emitLine("if(0==scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
      self.emitter.emitLine(self.curToken.text + " = 0;")
      self.emitter.emit("scanf(\"%")
      self.emitter.emitLine("*s\");")
      self.emitter.emitLine("}")
      self.match(TokenType.IDENT)
    
    # Invalid Statement
    else:
      self.abort("Invalid Statement at " + self.curToken.text + " (" + self.curToken.kind.name + ")")

    # A Newline.
    self.nl()

  def nl(self):
    #requires at least one newline
    self.match(TokenType.NEWLINE)
    # Extra newlines are not discriminated against
    while self.checkToken(TokenType.NEWLINE):
      self.nextToken()

  def expression(self):
    self.term() #not defined yet
    # It can have 0 or more +/- and expressions
    while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
      self.emitter.emit(self.curToken.text)
      self.nextToken()
      self.term()

  # term ::= unary {("/" | "*")}
  def term(self):
    self.unary()
    # It can have 0 or more * or / and expressions
    while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
      self.emitter.emit(self.curToken.text)
      self.nextToken()
      self.unary()
    
  # unary ::= ['+' | '-'] primary
  def unary(self):
    # optional unary +/-
    if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
      self.emitter.emit(self.curToken.text)
      self.nextToken()
    self.primary()

  # primary ::= number | ident
  def primary(self):
    if self.checkToken(TokenType.NUMBER):
      self.emitter.emit(self.curToken.text)
      self.nextToken()
    elif self.checkToken(TokenType.IDENT):
      #Ensure variable exists:
      if self.curToken.text not in self.symbols:
        self.abort("Referencing variable before assignment: " + self.curToken.text)
      self.emitter.emit(self.curToken.text)
      self.nextToken()
    else: 
      # Error: 
      self.abort("Unexpected token at " + self.curToken.text)

  def isComparisonOperator(self):
    return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

  def comparison(self):
    self.expression()
    # Must have one comparison operator
    if self.isComparisonOperator():
      self.emitter.emit(self.curToken.text)
      self.nextToken()
      self.expression()
    else:
      self.abort("Expected comparison operator at: " + self.curToken.text)

    #Can have 0 or more comparison operator and expressions:
    while self.isComparisonOperator():
      self.emitter.emit(self.curToken.text)
      self.nextToken()
      self.expression()

    