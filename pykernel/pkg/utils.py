import sys

def printi(msg):
    print(msg, file=sys.__stdout__)

def printe(msg):
    print(msg, file=sys.__stderr__)

def sendi(msg):
    print(msg, file=sys.stdout)

def sende(msg):
    print(msg, file=sys.stderr)