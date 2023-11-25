import enum
import sys

class Token:
  def __init__(self, tokenText, tokenKind):
    self.text = tokenText #The actual text of the token. Used for identifiers, strings, and nums.
    self.kind = tokenKind #The type of token it is

  @staticmethod #does not receive an implicit first argument
  def checkIfKeyword(tokenText):
    for kind in TokenType:
      #all keyword enum values must be within 100 (inclusive) and 200
      if kind.name == tokenText and kind.value >= 100 and kind.value < 200:
        return kind
    return None

#TokenType is our enum for all the types of tokens:
class TokenType(enum.Enum):
  EOF = -1
  NEWLINE = 0
  NUMBER = 1
  IDENT = 2 
  STRING = 3
  # KEYWORDS
  LABEL = 101
  GOTO = 102
  PRINT = 103
  INPUT = 104
  LET = 105
  IF = 106
  THEN = 107
  ENDIF = 108
  WHILE = 109
  REPEAT = 110
  ENDWHILE = 111
  # Operators.
  EQ = 201
  PLUS = 202
  MINUS = 203
  ASTERISK = 204
  SLASH = 205
  EQEQ = 206
  NOTEQ = 207
  LT = 208
  LTEQ = 209
  GT = 210
  GTEQ = 211

class Lexer:
  def __init__(self, source):
    self.source = source + '\n' # The source code that will be lexed as a string. Appending a new line makes it easier to parse/lex the last token/statement
    self.curChar = '' #current character in string
    self.curPos = -1 #Current position in the string (0-indexed). Used instead of string[index] format as it avoids bound-checking
    self.nextChar()

  # Function to process next character
  def nextChar(self):
    self.curPos += 1
    if self.curPos >= len(self.source):
      self.curChar = '\0' #end of the file marker
    else:
      self.curChar = self.source[self.curPos] #the current character

  # Function to return the lookahed character
  def peek(self):
    if self.curPos + 1 >= len(self.source): #if self.curPos is the last character (so self.curPos + 1 >= len(self.source)), return the EOF marker
      return '\0' #EOF marker
    return self.source[self.curPos+1]

  # Invalid token found, print error message and exit
  def abort(self, message):
    sys.exit("Lexing Error. " + message)

  # Skip whitespace except newlines, which we will use to indicate the end of a statement
  def skipWhitespace(self):
    while self.curChar == ' ' or self.curChar == '\t' or self.curChar == '\r':
      self.nextChar()

  # Skip comments in the code
  def skipComment(self):
    if self.curChar == '#':
      while self.curChar != '\n':
        self.nextChar()

  # Return the next token
  def getToken(self):
    #Check the first char of the token to see if we can determine the type of token it is
    # If it is a multiple character operator, number, identifier, or keyword then we will process the rest
    self.skipWhitespace()
    self.skipComment()
    token = None

    if self.curChar == '+':
      token = Token(self.curChar, TokenType.PLUS)
    elif self.curChar == '-':
      token = Token(self.curChar, TokenType.MINUS) #minus token
    elif self.curChar == '*':
      token = Token(self.curChar, TokenType.ASTERISK) #asterisk token
    elif self.curChar == '/':
      token = Token(self.curChar, TokenType.SLASH) #slash token
    elif self.curChar == '\n':
      token = Token(self.curChar, TokenType.NEWLINE) # Newline token
    elif self.curChar == '=':
      if self.peek() == '=':
        lastChar = self.curChar
        self.nextChar()
        token = Token(lastChar + self.curChar, TokenType.EQEQ)
      else:
        token = Token(self.curChar, TokenType.EQ)
    elif self.curChar == '>':
      if self.peek() == '=':
        lastChar = self.curChar
        self.nextChar()
        token = Token(lastChar + self.curChar, TokenType.GTEQ)
      else:
        token = Token(self.curChar, TokenType.GT)
    elif self.curChar == "<":
      if self.peek() == "=":
        lastChar = self.curChar
        self.nextChar()
        token = Token(lastChar + self.curChar, TokenType.LTEQ)
      else:
        token = Token(self.curChar, TokenType.LT)
    elif self.curChar == '!':
      if self.peek() == '=':
        lastChar = self.curChar
        self.nextChar()
        token = Token(lastChar+self.curChar, TokenType.NOTEQ)
      else:
        self.abort("Expected !=,  got !" + self.peek())
    elif self.curChar == '\"':
      # Get charas bet. quotes
      self.nextChar()
      startPos = self.curPos
      
      while self.curChar != '\"':
        # No special characters allowed in the string. No escape characters, newlines, tabs, or %.
        # Will be using C's printf on this string.
        if self.curChar == '\r' or self.curChar == '\n' or self.curChar == '\t' or self.curChar == "%" or self.curChar =='\\':
          self.abort("Illegal character in string.")
        self.nextChar()
      
      tokText = self.source[startPos:self.curPos]
      token = Token(tokText, TokenType.STRING)
    elif self.curChar.isdigit():
      # Leading character is a digit, so it has to be a number
      # Get all consec. digits and decimal point if there is one
      startPos = self.curPos

      while self.peek().isdigit():
        self.nextChar()
      if self.peek() == '.':
        self.nextChar()
        # It has to have at least one digit after the decimal point.
        if not self.peek().isdigit():
          #Error time :)
          self.abort("Illegal character in number.")
        while self.peek().isdigit():
          self.nextChar()
      
      tokText = self.source[startPos : self.curPos + 1] # +1 because slicing isn't inclusive of end.
      token = Token(tokText, TokenType.NUMBER)
    elif self.curChar.isalpha():
      #leading character is a letter, so this means it is an identifier or keyword.
      #Get all consecutive alpha numeric characters
      startPos = self.curPos
      while self.peek().isalnum():
        self.nextChar()
      tokText = self.source[startPos : self.curPos+1]
      keyword = Token.checkIfKeyword(tokText)
      if keyword == None:
        token = Token(tokText, TokenType.IDENT)
      else:
        token = Token(tokText, keyword)
    elif self.curChar == '\0':
      token = Token(self.curChar, TokenType.EOF) # EOF Token
    else:
      self.abort("Unknown token: " + self.curChar)
     
    self.nextChar()
    return token