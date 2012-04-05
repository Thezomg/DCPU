import re

types = {
    'none': 0,
    'function_def': 1,
    'function_call': 2,
    'variable_def': 3,
    'variable': 4,
    


class Token:
    def __init__(self, type):
        self.children = []
        self.parameters = []
        self.type = types['none']

class Lexer:
   
   def __init__(self, code):
       self.code = code
       self.prev = None
       self.curr = None
       self.prevChar = ''
       self.currChar = ''
       
   def parse(self):
       for c in code:
           self.currChar = c
       
   def __repr__(self):
       return code
       