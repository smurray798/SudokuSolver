#!/bin/bash

pyinstaller -F python/evaluate.py
cp dist/evaluate .
rm -rf evaluate.spec dist build
