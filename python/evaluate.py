#!/usr/bin/env python3

from progressbar import ProgressBar, Percentage, Bar, ETA	# progressbar2 (install with pip install progressbar2)
import argparse
from os.path import isfile

from SudokuSolver import SudokuSolver

# Get the arguments
parser = argparse.ArgumentParser()

parser.add_argument(
	'sudokuPuzzlesFile',
	help='File containing many Sudoku puzzles, each on a line of 81 characters'
)

args = parser.parse_args()

conflictPuzzlesPath = 'conflictPuzzles.txt'
conflictTranscriptsPath = 'conflictTranscripts.txt'

# Count the number of lines in the file
if not isfile(args.sudokuPuzzlesFile):
	print('Cannot open', args.sudokuPuzzlesFile)
	exit(1)

totalCount = sum(1 for line in open(args.sudokuPuzzlesFile))

# Load the Sudoku puzzles from the Ruud test set and try to solve them
solver = SudokuSolver()

solvedCount = 0
unsolvedCount = 0
conflictCount = 0

fConflictPuzzles = open(conflictPuzzlesPath, 'w')
fConflictTranscripts = open(conflictTranscriptsPath, 'w')

with open(args.sudokuPuzzlesFile, 'r') as f:
	puzzleString = f.readline().strip()

	pbar = ProgressBar(widgets=['Evaluating: ', Percentage(), ' ', Bar(), ' ', ETA()])
	pbar.start(max_value=totalCount)
	i = 0
	
	while puzzleString:
		solver.Setup(puzzleString=puzzleString)
		solver.Solve(createSteps=False)

		if solver.Puzzle.Solved:
			solvedCount += 1
		elif solver.Puzzle.Conflicting:
			conflictCount += 1
			solver.Setup(puzzleString=puzzleString)
			solver.Solve(createSteps=True)
			fConflictPuzzles.write(puzzleString + '\n')
			fConflictTranscripts.write(solver.GetTranscript(includePuzzles=False) + '\n' * 10)
		else:
			unsolvedCount += 1
		
		i += 1
		pbar.update(i)
		
		puzzleString = f.readline().strip()
pbar.finish()

fConflictPuzzles.close()
fConflictTranscripts.close()

print('Tested', totalCount, 'Sudoku puzzles')
print('Solved', solvedCount, 'or', 100 * solvedCount / totalCount, '%')
print('Did not solve', unsolvedCount, 'or', 100 * unsolvedCount / totalCount, '%')
print('There were', conflictCount, 'errors, or', 100 * conflictCount / totalCount, '%')