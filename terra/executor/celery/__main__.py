#!/usr/bin/env python

from os import environ as env
from . import app

def main():
  app.start()

if __name__ == '__main__':  # pragma: no cover
  main()
