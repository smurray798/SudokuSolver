#!/usr/bin/env python3

from python.SudokuSolver import SudokuSolver

solver = SudokuSolver()
solver.Setup(puzzlePath='puzzles/3DMedusaRule6.txt')

solver.Solve()

print(solver.ToStringConsole())

with open('transcript.txt', 'w') as f:
	f.write(solver.GetTranscript(includePuzzles=False))
