#!/usr/bin/env python3

import argparse, os
from itertools import combinations
from collections import Counter
from enum import Enum

# Instruction collected from https://www.sudokuwiki.org/Getting_Started

SudokuGroupType = Enum('SudokuGroupType', 'Row Column Box')

class SudokuCell():
	# Public Fields
	Index = None
	RowIndex = None
	ColumnIndex = None
	BoxIndex = None

	Solved = None
	Original = None
	Conflicting = None

	Value = None
	Candidates = None

	Row = None
	Column = None
	Box = None
	Groups = None
	SharedGroupCells = None

	StepEliminatedCandidates = None

	idStr = None



	# Public Properties
	@property
	def HasStepEliminatedCandidates(self):
		return (len(self.StepEliminatedCandidates) > 0)
	
	@property
	def ID(self):
		return self.GetID()
	
	@property
	def CandidateCount(self):
		return len(self.Candidates)
	
	

	# Constructor
	def __init__(self, index:int):
		if not (0 <= index <= 80):
			raise ValueError('index must be [0, 80]')
		
		self.Index = index
		self.RowIndex = index // 9
		self.ColumnIndex = index % 9
		self.BoxIndex = (self.ColumnIndex // 3) + ((self.RowIndex // 3) * 3)

		self.Reset()
		return



	# Public Methods
	def CopyTo(self, dst):
		if type(dst) != SudokuCell:
			raise ValueError('dst must be of type SudokuCell')
		if self.Index != dst.Index:
			raise Exception('dst.Index must be identical to self.Index')

		dst.Solved = self.Solved
		dst.Original = self.Original
		dst.Conflicting = self.Conflicting

		dst.Value = self.Value
		dst.Candidates = self.Candidates.copy()
		dst.StepEliminatedCandidates = self.StepEliminatedCandidates.copy()

		return

	def Reset(self):
		self.Solved = False
		self.Original = False
		self.Conflicting = False

		self.Value = 0
		self.Candidates = set(range(1, 10))
		self.StepEliminatedCandidates = set()

		self.Row = None
		self.Column = None
		self.Box = None
		self.Groups = set()

		return

	def GetID(self):
		if type(self.idStr) == str:
			if len(self.idStr) == 2:
				return self.idStr

		if (not (0 <= self.RowIndex <= 8)) or (not (0 <= self.ColumnIndex <= 8)):
			self.idStr = None
			return None
		
		# Rows are A to I
		# Columns are 1 to 9
		self.idStr = chr((self.RowIndex) + ord('A')) + chr(self.ColumnIndex + ord('1'))
		return self.idStr
	
	def __str__(self):
		return self.ID
	
	def IsCandidate(self, candidate:int):
		if self.CandidateCount <= 1:
			return False
		return (candidate in self.Candidates)
	
	def AreAllCandidates(self, candidates:set):
		if self.CandidateCount <= 1:
			return False
		return candidates.issubset(self.Candidates)
	
	def EliminateCandidate(self, candidate:int):
		# Returns True if the candidate was actually removed from the Candidates list, returns False otherwise
		eliminated = False
		if candidate in self.Candidates:
			self.Candidates.discard(candidate)
			eliminated = True
			self.StepEliminatedCandidates.add(candidate)
		return eliminated
		
	def EliminateCandidates(self, candidates:set):
		# Returns True if any candidate was actually removed from the Candidates list, returns False otherwise
		changed = False
		for candidate in candidates:
			if self.EliminateCandidate(candidate):
				changed = True
		return changed
	
	def SetValue(self, value:int, isOriginal:bool=False):
		if not(1 <= value <= 9):
			raise ValueError('value must be [0, 8]')
		if self.Solved:
			if self.Value != value:
				raise Exception('Cannot set value for SudokuCell once it has already been set to a different value')
		self.Value = value
		self.Solved = True
		self.Candidates = {value}

		self.Original = isOriginal

		return
	
	def GetSortedCandidates(self):
		return sorted(self.Candidates)
	
	def ToString(self):
		if self.Solved:
			return 'Cell ' + self.ID + ' Solved: ' + str(self.Value)
		return 'Cell ' + self.ID + ' Candidates: ' + str(self.GetSortedCandidates)[1:-1]
		






class SudokuGroup():
	Type = None
	Index = None

	Cells = None

	ID = None

	@property
	def Number(self):
		return self.Index + 1

	@property
	def SolvedCount(self):
		solvedCount = 0
		for cell in self.Cells:
			if cell.Solved:
				solvedCount += 1
		return solvedCount
	
	@property
	def UnsolvedCount(self):
		unsolvedCount = 0
		for cell in self.Cells:
			if not cell.Solved:
				unsolvedCount += 1
		return unsolvedCount

	@property
	def Solved(self):
		return (self.SolvedCount == 9)

	@property
	def UnsolvedCandidates(self):
		s = set()
		for cell in self.Cells:
			s = s.union(cell.Candidates)
		return s
	


	# Constructor
	def __init__(self, groupType:SudokuGroupType, index:int):
		if not (0 <= index <= 8):
			raise ValueError('index must be [0, 8]')
		if groupType not in [SudokuGroupType.Row, SudokuGroupType.Column, SudokuGroupType.Box]:
			raise ValueError('groupType must be a SudokuGroupType enum with a value of either Row, Column, or Box')

		self.Type = groupType
		self.Index = index
		
		if groupType == SudokuGroupType.Row:
			self.ID = 'Row ' + chr(self.Index + ord('A'))
		elif groupType == SudokuGroupType.Column:
			self.ID = 'Column ' + chr(self.Index + ord('1'))
		elif groupType == SudokuGroupType.Box:
			self.ID = 'Box ' + chr(self.Index + ord('1'))
		else:
			raise ValueError('Invalid groupType')

		return
	
	def __str__(self):
		return self.ID
	


	# Public Methods
	def Populate(self, cells:set):
		if self.Cells is not None:
			raise Exception('Cannot re-Populate SudokuGroup')

		if len(cells) != 9:
			raise ValueError('cells must contain 9 unique SudokuCell objects')

		for cell in cells:
			if type(cell) != SudokuCell:
				raise ValueError('cells must contain 9 unique SudokuCell objects')
			if self.Type == SudokuGroupType.Row:
				if cell.RowIndex != self.Index:
					raise Exception('A SudokuCell in cells is not a member of the correct row group')
			elif self.Type == SudokuGroupType.Column:
				if cell.ColumnIndex != self.Index:
					raise Exception('A SudokuCell in cells is not a member of the correct column group')
			elif self.Type == SudokuGroupType.Box:
				if cell.BoxIndex != self.Index:
					raise Exception('A SudokuCell in cells is not a member of the correct box group')
		
		# Assign each cell to the proper group
		self.Cells = cells
		for cell in self.Cells:
			if self.Type == SudokuGroupType.Row:
				cell.Row = self
			elif self.Type == SudokuGroupType.Column:
				cell.Column = self
			elif self.Type == SudokuGroupType.Box:
				cell.Box = self
			cell.Groups.add(self)
		
		return

	def GetCellsWithCandidate(self, candidate):
		return set([cell for cell in self.Cells if cell.IsCandidate(candidate)])







class SudokuPuzzle():
	# Public Fields
	Cells = None

	Rows = None
	Columns = None
	Boxes = None
	AllGroups = None

	SinglesChains = None
	SuperChains = None

	@property
	def Solved(self):
		solved = True
		for cell in self.Cells:
			if not cell.Solved:
				solved = False
				break
		return solved
	
	@property
	def SolvedCellsCount(self):
		count = 0
		for cell in self.Cells:
			if cell.Solved:
				count += 1
		return count
	
	@property
	def Conflicting(self):
		conflicting = False
		for cell in self.Cells:
			if cell.Conflicting:
				conflicting = True
				break
		return conflicting



	# Constructor
	def __init__(self):
		# Create the cells
		self.Cells = [SudokuCell(i) for i in range(81)]

		# Create the groups
		self.Rows = [SudokuGroup(SudokuGroupType.Row, i) for i in range(9)]
		self.Columns = [SudokuGroup(SudokuGroupType.Column, i) for i in range(9)]
		self.Boxes = [SudokuGroup(SudokuGroupType.Box, i) for i in range(9)]
		self.AllGroups = self.Rows + self.Columns + self.Boxes
		
		# Put the cells into their groups
		for i in range(9):
			self.Rows[i].Populate(set([cell for cell in self.Cells if cell.RowIndex == i]))
			self.Columns[i].Populate(set([cell for cell in self.Cells if cell.ColumnIndex == i]))
			self.Boxes[i].Populate(set([cell for cell in self.Cells if cell.BoxIndex == i]))
		
		# For each cell, make a list of all other cells (exculding the cell itself) that share at least one group
		for cell in self.Cells:
			cell.SharedGroupCells = cell.Row.Cells | cell.Column.Cells | cell.Box.Cells
			cell.SharedGroupCells.discard(cell)

		return



	# Public Methods
	def Copy(self):
		cpy = SudokuPuzzle()
		self.CopyTo(cpy)
		return cpy
	
	def CopyTo(self, dst):
		if type(dst) != SudokuPuzzle:
			raise ValueError('dst must be of type SudokuPuzzle')
		for i, cell in enumerate(self.Cells):
			cell.CopyTo(dst.Cells[i])
		return
	
	def Reset(self):
		for cell in self.Cells:
			cell.Reset()
		return
		
	def ClearStepEliminatedCandidates(self):
		for cell in self.Cells:
			cell.StepEliminatedCandidates.clear()
		return
	
	def GetCell(self, rowNumber=None, columnNumber=None, idStr=None):
		if (rowNumber is not None) and (columnNumber is not None):
			index = (columnNumber - 1) + ((rowNumber - 1) * 9)
			if not (0 <= index <= 80):
				return None
			cell = self.Cells[index]
			if cell.Index != index:
				raise Exception('Cells are out of order')
			return cell
		elif type(idStr) == str:
			for cell in self.Cells:
				if cell.ID == idStr:
					return cell
		return None

	def ToString(self, blankChar:str='.', newlines:bool=False):
		# Relies on the cell order not being re-arranged
		s = ''
		for i, cell in enumerate(self.Cells):
			s += str(cell.Value)
			if newlines and ((i % 9) == 8):
				s += '\n'
		if (len(blankChar) == 1) and (blankChar not in '123456789\n\r'):
			s = s.replace('0', blankChar)
		return s

	def ToStringConsole(self, displayRowCol:bool=True):
		s = self.ToString(blankChar=' ')
		rowdivider = ' ' + '-' * 23 + ' \n'
		if displayRowCol:
			rowdivider = '  ' + rowdivider

		if displayRowCol:
			s2 = '    1 2 3   4 5 6   7 8 9  \n' + rowdivider
		else:
			s2 = rowdivider

		for rowindex in range(9):
			if displayRowCol:
				s2 += chr(rowindex + ord('A')) + ' '
			
			s2 += '|'
			for colblockindex in [0, 3, 6]:
				index = colblockindex + (9 * rowindex)
				block = ' ' + s[index + 0] + ' ' + s[index + 1] + ' ' + s[index + 2] + ' '
				s2 += block + '|'
			s2 += '\n'
			if (rowindex % 3 == 2):
				s2 += rowdivider
		
		return s2
	
	def LoadFromString(self, s:str):
		# If newlines exist, it is required to have 9 lines each with 9 characters
		if ('\n' in s) or ('\r' in s):
			lines = s.splitlines()
			if len(lines) != 9:
				return False, 'There must be exactly 9 lines in the load string (or none at all), but there are ' + str(len(lines)) + ' lines'
			s = ''
			for i, line in enumerate(lines):
				if len(line) != 9:
					return False, 'There must have exactly 9 characters in each line in the load string, but line ' + str(i + 1) + ' has ' + str(len(line)) + ' characters'
				s += line

		# Check string length
		if len(s) != 81:
			return False, 'Sudoku size must be 81, but the load string says its size is ' + str(len(s))

		# Replace spaces and 0s with dots
		s = s.replace(' ', '.').replace('0', '.')

		# Check for invalid characters
		for c in s:
			if c not in '.123456789':
				return False, 'Found invalid character "' + c + '" in load string'
		
		# Set each cell
		self.Reset()
		for i, cell in enumerate(self.Cells):
			if i != cell.Index:
				raise Exception('Cells are out of order')
			c = s[i]
			if c != '.':
				value = ord(c) - ord('0')
				cell.SetValue(value, isOriginal=True)
		
		return True, 'Successfully loaded Sudoku puzzle from string'
	
	def LoadFromFile(self, path:str):
		if not os.path.isfile(path):
			return False, path + ' does not exist or is not a file'
		
		s = None
		with open(path, 'r') as f:
			s = f.read()

		return self.LoadFromString(s)







class SudokuTechniqueData():
	Technique = ''
	
	TechniqueCells = set()
	ChangedCells = set()
	TechniqueCandidates = set()

	Description = ''

	
	ChangesStr = ''
	
	@property
	def TechniqueCellsStr(self):
		s = ''
		s += 'Technique Cell'
		if len(self.TechniqueCells) > 1:
			s += 's'
		s += ': '
		s += self.ListToString(self.TechniqueCells)
		return s
	
	@property
	def ChangedCellsStr(self):
		s = ''
		s += 'Changed Cell'
		if len(self.ChangedCells) > 1:
			s += 's'
		s += ': '
		s += self.ListToString(self.ChangedCells)
		return s
	
	@property
	def TechniqueCandidatesStr(self):
		s = ''
		s += 'Technique Candidate'
		if len(self.ChangedCells) > 1:
			s += 's'
		s += ': '
		s += self.ListToString(self.TechniqueCandidates)
		return s
	
	@property
	def ChangesDescription(self):
		changeStrings = []

		for candidate in range(1, 10):
			changedCellsForCandidate = set()
			for cell in self.ChangedCells:
				if candidate in cell.StepEliminatedCandidates:
					changedCellsForCandidate.add(cell)
			
			if len(changedCellsForCandidate) > 0:
				s = 'Eliminated candidate ' + str(candidate) + ' from cell'
				if len(changedCellsForCandidate) > 1:
					s += 's'
				s += ' '
				s += self.ListToString(changedCellsForCandidate)
				changeStrings.append(s)
		
		if len(changeStrings) == 0:
			return "No changes"
		
		changes = ''
		for changeString in changeStrings:
			changes += changeString + '\n'
		self.ChangesStr = changes[:-1]
		return self.ChangesStr
	
	def __init__(self, technique=None, techniqueCells=None, changedCells=None, techniqueCandidates=None, description=None):
		if technique is not None:
			if techniqueCells is None:
				techniqueCells = set()
			if changedCells is None:
				changedCells = set()
			if techniqueCandidates is None:
				techniqueCandidates = set()
			
			self.Set(technique, techniqueCells, changedCells, techniqueCandidates)
			if description is not None:
				self.Description = description
		return

	def Set(self, technique:str, techniqueCells:set, changedCells:set, techniqueCandidates:set):
		for cell in techniqueCells:
			if type(cell) != SudokuCell:
				raise Exception('All elements in techniqueCells must be of type SudokuCell')
		
		for cell in changedCells:
			if type(cell) != SudokuCell:
				raise Exception('All elements in changedCells must be of type SudokuCell')
		
		for candidate in techniqueCandidates:
			if type(candidate) != int:
				raise Exception('All candidates in techniqueCandidates must be ints [1, 9]')
			if not (1 <= candidate <= 9):
				raise Exception('All candidates in techniqueCandidates must be ints [1, 9]')

		self.Technique = technique
		self.TechniqueCells = techniqueCells
		self.ChangedCells = changedCells
		self.TechniqueCandidates = techniqueCandidates
		return

	@staticmethod
	def ListToString(l):
		l = sorted([str(el) for el in l])
		if len(l) == 0:
			return ''
		if len(l) == 1:
			return str(list(l)[0])
		if len(l) == 2:
			return str(l[0]) + ' and ' + str(l[1])
		s = ''
		for i, element in enumerate(l):
			if i == (len(l) - 1):
				s += 'and ' + element
			else:
				s += element + ', '
		return s
	
class SudokuStep():
	def __init__(self, puzzle:SudokuPuzzle, techniqueData:SudokuTechniqueData):
		self.Puzzle = puzzle
		self.TechniqueData = techniqueData
		return

class SudokuSinglesChain():
	Candidate = None

	Links = None
	Colors = None
	
	Cells = None

	ClosedLoop = None
	Perimeter = None
	Rectangular = None

	colorsWereSwapped = False
	
	@staticmethod
	def CreateAllSinglesChains(puzzle:SudokuPuzzle):
		allSinglesChains = []

		for candidate in range(1, 10):
			allSinglesChains += SudokuSinglesChain.CreateSinglesChainsForCandidate(puzzle, candidate)
		return allSinglesChains
	
	@staticmethod
	def CreateSinglesChainsForCandidate(puzzle:SudokuPuzzle, candidate:int):
		# Creates all singles chains for the candidates in the puzzle, fully colorized
		# A chain link is established between two cells when a group contains the candidate only in those two cells
		# A singles chain is the set of all links for the candidate that share a cell with at least one other link in the chain
		# Each cell is assigned one of two colors, and all cells directly connected to it by a single link are assigned the other color

		if not (1 <= candidate <= 9):
			raise ValueError('candidate must be [1, 9]')

		# Make a list of all chain links (not necessarily in the same chain) for the candidate
		# Cycle through all groups looking for only two appearances of the candidate
		allLinks = []
		for g in puzzle.AllGroups:
			link = g.GetCellsWithCandidate(candidate)
			if len(link) != 2:
				continue
			
			# Make sure the link does not already exist in links
			if link not in allLinks:
				allLinks.append(link)
		
		# Make a list of all chains
		# Start by assuming all links are their own chain, then merge chains into one for chains that share at least one common cell
		chains = [[link] for link in allLinks]

		# Merge the chains until they cannot be merged any more
		mergedChain = True
		while mergedChain:
			mergedChain = False

			for chain1, chain2 in combinations(chains, 2):
				# Get all cells in each chain
				chain1cells = set().union(*chain1)
				chain2cells = set().union(*chain2)

				# If the chains have any cells in common, they can be merged together
				if len(chain1cells.intersection(chain2cells)) >= 1:
					# Merge the chains into one chain
					chain = chain1 + chain2

					# Remove the old chains and add the new one
					chains.remove(chain1)
					chains.remove(chain2)
					chains.append(chain)
					mergedChain = True
					break
		
		# Colorize the chain. Each cell is one color, and all cells directly connected to it by a single link are the opposite color
		singlesChains = []
		for chain in chains:
			# Each chain has exactly two colors
			colors = [set(), set()]
			uncoloredCells = set().union(*chain)
			coloredCells = set()

			# Arbitrarily put one of the cells in a color
			cell = uncoloredCells.pop()
			colors[0].add(cell)
			coloredCells.add(cell)

			# Keep assigning cells to a color until they are all assigned
			while len(uncoloredCells) > 0:
				performedAssignment = False
				# Pick a cell that has already been colored
				for coloredCell in coloredCells:
					# Get all cells linked to this cell
					linkedCells = set()
					for link in chain:
						if coloredCell in link:
							linkedCells = linkedCells.union(link)
					linkedCells.remove(coloredCell)

					# Cells connected to the colored cell go in the other color
					color = 0
					if coloredCell in colors[0]:
						color = 1
					
					for cell in linkedCells:
						if cell in uncoloredCells:
							uncoloredCells.remove(cell)
							colors[color].add(cell)
							coloredCells.add(cell)
							performedAssignment = True
					if performedAssignment:
						break
			
			# Count the number of times each cell appears in the links
			cellCounts = dict([(cell, 0) for cell in coloredCells])
			for link in chain:
				for cell in link:
					cellCounts[cell] += 1
			
			closedLoop = True
			perimeter = True
			for cell in cellCounts:
				if cellCounts[cell] == 1:
					closedLoop = False
				if cellCounts[cell] != 2:
					perimeter = False
			rectangular = (len(cellCounts) == 4) and perimeter
			
			# The chain is now fully colored. Create an object and add it to the list
			singlesChain = SudokuSinglesChain()
			singlesChain.Candidate = candidate
			singlesChain.Links = chain
			singlesChain.Colors = colors
			singlesChain.Cells = coloredCells
			singlesChain.ClosedLoop = closedLoop
			singlesChain.Perimeter = perimeter
			singlesChain.Rectangular = rectangular

			singlesChains.append(singlesChain)
		return singlesChains

	def SwapColors(self):
		if self.colorsWereSwapped:
			raise Exception('Colors have already been swapped, cannot swap them again')

		self.Colors.reverse()
		return
	
	def LinksToColorizedStringList(self):
		linksStrings = []
		for link in self.Links:
			if len(link) == 2:
				link = list(link)
				if link[0] in self.Colors[1]:
					link.reverse()
				linksStrings.append('(Red ' + str(link[0]) + ', Blue ' + str(link[1]) + ')')
			elif len(link) == 1:
				cell = list(link)[0]
				colorStr = None
				if cell in self.Colors[0]:
					colorStr = 'Red'
				else:
					colorStr = 'Blue'
				linksStrings.append('(' + colorStr + ' ' + str(cell) + ')')
		return linksStrings
	
	def ChainToString(self):
		return SudokuTechniqueData.ListToString(self.LinksToColorizedStringList())
	
class SudokuSuperChain():
	SinglesChains = None
	Cells = None
	LinkCells = None
	Candidates = None

	@staticmethod
	def CreateSuperChains(allSinglesChains:list):
		# A super chain is formed from several singles chains linked by bi-value cells shared by two (or more) singles chains

		# Start by making each super chain have only one singles chain
		chains = [[singlesChain] for singlesChain in allSinglesChains]

		# Merge the super chains until they no longer can be merged. Super chains can be merged if they share a cell with exactly two candidates
		mergedChain = True
		while mergedChain:
			mergedChain = False

			for superChain1, superChain2 in combinations(chains, 2):
				# Get all cells in each super chain that have exactly two candidates
				superChain1cells = set([cell for cell in set().union(*[singlesChain.Cells for singlesChain in superChain1]) if cell.CandidateCount == 2])
				superChain2cells = set([cell for cell in set().union(*[singlesChain.Cells for singlesChain in superChain2]) if cell.CandidateCount == 2])

				# If the super chains have any bi-candidate cells in common, they can be merged together
				if len(superChain1cells.intersection(superChain2cells)) >= 1:
					# Merge the super chains into one super chain
					superChain = superChain1 + superChain2

					# Remove the old super chains and add the new one
					chains.remove(superChain1)
					chains.remove(superChain2)
					chains.append(superChain)
					mergedChain = True
					break

		# Create the super chains list
		superChains = []
		for singlesChains in chains:
			if len(singlesChains) <= 1:
				continue
			superChain = SudokuSuperChain()
			superChain.SinglesChains = singlesChains
			superChain.Cells = set().union(*[singlesChain.Cells for singlesChain in singlesChains])
			superChain.Candidates = set().union([singlesChain.Candidate for singlesChain in singlesChains])
			superChain.LinkCells = set()
			for cell in superChain.Cells:
				if cell.CandidateCount != 2:
					continue
				isLinkCell = False
				for chain1, chain2 in combinations(singlesChains, 2):
					if (cell in chain1.Cells) and (cell in chain2.Cells):
						superChain.LinkCells.add(cell)
						isLinkCell = True
						break
				if isLinkCell:
					continue
			
			# Search for bi-value cells in the chain that may not be fully colorized
			for cell in [cell for cell in superChain.Cells if (cell.CandidateCount == 2) and (cell not in superChain.LinkCells)]:
				# Determine which candidate is colored and what color it is
				coloredCandidate = None
				coloredCandidateColorNum = None
				for colorNum in range(2):
					for singlesChain in superChain.SinglesChains:
						if cell in singlesChain.Colors[colorNum]:
							coloredCandidate = singlesChain.Candidate
							coloredCandidateColorNum = colorNum
							break
					if coloredCandidate is not None:
						break
				
				# Create a new singles chain with only the bi-value cell in it, and colorize the other candidate the opposite color
				singlesChain = SudokuSinglesChain()
				singlesChain.Candidate = list(cell.Candidates.difference({coloredCandidate}))[0]
				singlesChain.Links = [{cell}]
				singlesChain.Colors = [set(), set()]
				singlesChain.Colors[(coloredCandidateColorNum + 1) % 2].add(cell)
				singlesChain.Cells = {cell}
				singlesChain.ClosedLoop = False
				singlesChain.Perimeter = False
				singlesChain.Rectangular = False
				
				superChain.SinglesChains.append(singlesChain)
				superChain.LinkCells.add(cell)

			superChains.append(superChain)

			# Colorize the super chain
			# Assume that the first singles chain in the super chain is colored correctly
			colorizedSinglesChains = {singlesChains[0]}
			uncolorizedSinglesChains = set(singlesChains[1:])

			# Keep assigning colors until there are no uncolored chains
			while len(uncolorizedSinglesChains) > 0:
				performedAssignment = False
				# Pick a chain that has not been colorized
				for uncolorizedSinglesChain in uncolorizedSinglesChains:
					# Pick a link cell in the uncolorized super chain
					for linkCell in uncolorizedSinglesChain.Cells.intersection(superChain.LinkCells):
						# Pick a chain that has been colorized that also contains the link cell
						for colorizedSinglesChain in [c for c in colorizedSinglesChains if linkCell in c.Cells]:
							# Link cells must be in opposite colors between the colorized chain and uncolorized chain
							if ((linkCell in uncolorizedSinglesChain.Colors[0]) and (linkCell in colorizedSinglesChain.Colors[0])) or ((linkCell in uncolorizedSinglesChain.Colors[1]) and (linkCell in colorizedSinglesChain.Colors[1])):
								# The uncolorized chain's colors are swapped. Swap them so that they are proper
								uncolorizedSinglesChain.SwapColors()
							# The uncolorized chain is now colorized
							colorizedSinglesChains.add(uncolorizedSinglesChain)
							uncolorizedSinglesChains.discard(uncolorizedSinglesChain)
							performedAssignment = True
							break
						if performedAssignment:
							break
					if performedAssignment:
						break
		
		return superChains
	
	def LinksToColorizedStringListOfLists(self):
		return [singlesChain.LinksToColorizedStringList() for singlesChain in self.SinglesChains]
	
	def ChainToString(self):
		return SudokuTechniqueData.ListToString(['{Candidate ' + str(singlesChain.Candidate) + ': ' + singlesChain.ChainToString() + '}' for singlesChain in self.SinglesChains])

class SudokuNiceLoop():
	Candidate = None
	Rule = None

	Chain = None	# A list of the ordered cells in the chain (the last cell will be equivalent to the first)
	StrongWeakPattern = None	# A list of numbers, either 1 (for strong link) or 0 (for weak link) corresponding to the strong-weak link pattern in the chain

	StrongLinks = None
	WeakLinks = None

	Cells = None

	@staticmethod
	def CreateAllNiceLoops(puzzle:SudokuPuzzle):
		allNiceLoops = []

		# Build the singles chains for the puzzle if they are not already built
		if puzzle.SinglesChains is None:
			puzzle.SinglesChains = SudokuSinglesChain.CreateAllSinglesChains(puzzle)

		for candidate in range(1, 10):
			# Find all strong and weak links for this candidate
			
			# All possible strong links are the links of all the singles chains for the candidate
			allStrongLinks = []
			cellsWithStrongLinks = set()
			for singlesChain in [singlesChain for singlesChain in puzzle.SinglesChains if singlesChain.Candidate == candidate]:
				for link in singlesChain.Links:
					allStrongLinks.append(link)
					cellsWithStrongLinks = cellsWithStrongLinks.union(link)
			
			if len(allStrongLinks) == 0:
				continue

			allCandidateCells = set([cell for cell in puzzle.Cells if cell.IsCandidate(candidate)])

			# Build a chain up until it forms a nice loop or it quits
			# Every nice loop must start (and end) with a strong link. Cycle through every strong link as a starting point
			for startingStrongLink in allStrongLinks:
				chain = [cell for cell in startingStrongLink]

				SudokuNiceLoop.recursiveNiceLoopBuilder(allNiceLoops, candidate, allCandidateCells, allStrongLinks, chain)

				chain = [chain[1], chain[0]]

				SudokuNiceLoop.recursiveNiceLoopBuilder(allNiceLoops, candidate, allCandidateCells, allStrongLinks, chain)
			
		return allNiceLoops
	
	@staticmethod
	def recursiveNiceLoopBuilder(allNiceLoops:list, candidate:int, allCandidateCells:set, allStrongLinks:list, chain:list):
		# The chain is incomplete. Cycle through each new cell from the allCells set that is not already part of the chain and that intersects with the old end cell
		for endCell in [cell for cell in allCandidateCells.intersection(chain[-1].SharedGroupCells) if cell not in chain[1:]]:
			# Add the next end cell to the end of the chain (do NOT do this in-place, or it will corrupt the recursion process)
			newChain = chain + [endCell]

			# If the last three links are all weak chains, skip this chain
			if len(newChain) >= 4:
				link = {newChain[-1], newChain[-2]}
				if link not in allStrongLinks:
					link = {newChain[-2], newChain[-3]}
					if link not in allStrongLinks:
						link = {newChain[-3], newChain[-4]}
						if link not in allStrongLinks:
							return
			
			# If the end cell is the same as the beginning cell, the chain is closed and complete
			if (len(newChain) >= 5) and (endCell == newChain[0]):
				# If this new chain contains the same cells as a chain already in the allNiceLoops list, then it is redundant and can be skipped
				cells = set(newChain)
				for niceLoop in allNiceLoops:
					if niceLoop.Cells == cells:
						return
				
				# Found a nice loop
				# Note that the nice loop is guaranteed to contain at least one strong link, but not guaranteed to have any more.
				
				# Determine if each link is strong or weak
				strongLinks = []
				weakLinks = []
				pattern = []
				hasBackToBackWeakLinks = False
				seriesWeakLinks = 0
				rule = 1
				for i in range(len(newChain) - 1):
					cell1 = newChain[i]
					cell2 = newChain[i + 1]
					link = {cell1, cell2}
					if link in allStrongLinks:
						strongLinks.append(link)
						pattern.append(1)
						seriesWeakLinks = 0
					else:
						weakLinks.append(link)
						pattern.append(0)
						seriesWeakLinks += 1
						if seriesWeakLinks == 2:
							if hasBackToBackWeakLinks:
								# More than one set of back-to-back weak links
								return
							if (len(cells) % 2) != 1:
								# A nice loop with back-to-back weak links must have an odd number of cells
								return
							hasBackToBackWeakLinks = True
						elif seriesWeakLinks >= 3:
							return
				if len(weakLinks) == 0:
					# A nice loop needs at least one weak link. If it has none, then a pointing pair would have already solved it
					return
				if (len(cells) % 2) == 0:
					# A nice loop with an even number of cells must alternate between strong and weak links
					for i in range(len(pattern)):
						if ((i % 2) == 0):
							if  (pattern[i] == 0):
								return
						else:
							pattern[i] = 0
				else:
					# A nice loop with an odd number of cells must alternate between strong and weak links except for in one place, where it is allowed to have back-to-back strong links or back-to-back weak links
					if hasBackToBackWeakLinks:
						rule = 3
						# Find the index of the second weak link in the back-to-back weak links
						for i in range(1, len(pattern)):
							if (pattern[i] == 0) and (pattern[i - 1]) == 0:
								# Make sure the loop alternates between strong and weak links starting at i
								for j in range(len(pattern)):
									if ((j % 2) == 1):
										if (pattern[(i + j) % len(pattern)] == 0):
											return
									else:
										pattern[(i + j) % len(pattern)] = 0
								break
					else:
						rule = 2
						# Find the index of the last strong link in a series of strong links that is even in number
						backToBackStrongLinksCount = 0
						for i in range(len(pattern) * 2):
							if pattern[i % len(pattern)] == 1:
								backToBackStrongLinksCount += 1
							else:
								if (backToBackStrongLinksCount % 2) == 0:
									# Found the index of the last strong link in a series of strong links that is even in number
									index = (i - 1) % len(pattern)
									for j in range(len(pattern)):
										if ((j % 2) == 0):
											if(pattern[(index + j) % len(pattern)]) == 0:
												return
										else:
											pattern[(index + j) % len(pattern)] = 0
									break
								backToBackStrongLinksCount = 0

					
				# Create the SudokuNiceLoop object and append it to allNiceLoops in-place
				niceLoop = SudokuNiceLoop()

				niceLoop.Candidate = candidate
				niceLoop.Rule = rule
				niceLoop.Chain = newChain
				niceLoop.StrongWeakPattern = pattern
				niceLoop.StrongLinks = strongLinks
				niceLoop.WeakLinks = weakLinks
				niceLoop.Cells = cells

				allNiceLoops.append(niceLoop)

				return

			# Call the next recursion
			SudokuNiceLoop.recursiveNiceLoopBuilder(allNiceLoops, candidate, allCandidateCells, allStrongLinks, newChain)

		return
	
	def ChainToString(self):
		s = ''
		onoff = '+'
		for i in range(len(self.Chain)):
			cell = self.Chain[i]
			s += onoff + str(self.Candidate) + '[' + str(cell) + ']'
			if i < (len(self.Chain) - 1):
				s += '<' + {0: 'w', 1: 's'}[self.StrongWeakPattern[i]] + '>'
			if onoff == '+':
				onoff = '-'
			else:
				onoff = '+'
		return s







class SudokuSolver():
	Puzzle = None
	OriginalPuzzle = None
	SolvedPuzzle = None

	Steps = None
	CreateSteps = None

	OrderedTechniques = None

	@property
	def Solved(self):
		return self.Puzzle.Solved

	def __init__(self):
		self.Puzzle = SudokuPuzzle()
		self.OriginalPuzzle = SudokuPuzzle()
		self.SolvedPuzzle = SudokuPuzzle()

		self.Steps = []

		self.OrderedTechniques = [	# Do NOT include 'Sudoku Rules' in this list!
			'Naked Single',
			'Hidden Single', 
			'Pointing Pair',
			'Pointing Triplet',
			'Naked Pair',
			'Hidden Pair',
			'Naked Triplet',
			'Hidden Triplet',
			'Naked Quad',
			'Hidden Quad',
			'Naked Quint',
			'X-Wing',
			'Singles Chain Rule 2',
			'Singles Chain Rule 4',
			'Swordfish',
			'Y-Wing',
			'XYZ-Wing',
			'Bi-Value Universal Grave',
			'XY-Chain',
			'3D Medusa Rule 1',
			'3D Medusa Rule 2',
			'3D Medusa Rule 3',
			'3D Medusa Rule 4',
			'3D Medusa Rule 5',
			'3D Medusa Rule 6',
			'Jellyfish',
			'Unique Rectangle',
			'X-Cycle',
			'WXYZ-Wing'
		]
		return

	def Reset(self):
		self.__init__()
	
	def Setup(self, puzzle=None, puzzleString=None, puzzlePath=None):
		self.Reset()

		if puzzle is not None:
			pass
		elif puzzleString is not None:
			puzzle = SudokuPuzzle()
			ret, err = puzzle.LoadFromString(puzzleString)
			if not ret:
				raise Exception(err)
		elif puzzlePath is not None:
			puzzle = SudokuPuzzle()
			ret, err = puzzle.LoadFromFile(puzzlePath)
			if not ret:
				raise Exception(err)
		if type(puzzle) != SudokuPuzzle:
			raise TypeError('puzzle must be of type SudokuPuzzle')
		
		puzzle.CopyTo(self.Puzzle)
		puzzle.CopyTo(self.OriginalPuzzle)
		originalTechniqueData = SudokuTechniqueData()
		originalTechniqueData.Technique = 'Original'

		originalStep = SudokuStep(self.OriginalPuzzle.Copy(), originalTechniqueData)
		self.Steps.append(originalStep)

		return

	def UseTechnique(self, technique:str):
		if technique == 'Sudoku Rules':
			return self.ScanSudokuRules()
		elif technique == 'Naked Single':
			return self.ScanNakedSingle()
		elif technique == 'Hidden Single':
			return self.ScanHiddenSingle()
		elif technique == 'Pointing Pair':
			return self.ScanPointingCombo(2)
		elif technique == 'Pointing Triplet':
			return self.ScanPointingCombo(3)
		elif technique == 'Naked Pair':
			return self.ScanNakedCombo(2)
		elif technique == 'Hidden Pair':
			return self.ScanHiddenCombo(2)
		elif technique == 'Naked Triplet':
			return self.ScanNakedCombo(3)
		elif technique == 'Hidden Triplet':
			return self.ScanHiddenCombo(3)
		elif technique == 'Naked Quad':
			return self.ScanNakedCombo(4)
		elif technique == 'Hidden Quad':
			return self.ScanHiddenCombo(4)
		elif technique == 'Naked Quint':
			return self.ScanNakedCombo(5)
		elif technique == 'X-Wing':
			return self.ScanXWingOrSwordfishOrJellyfish(2)
		elif technique == 'Singles Chain Rule 2':
			return self.ScanSinglesChainRule2()
		elif technique == 'Singles Chain Rule 4':
			return self.ScanSinglesChainRule4()
		elif technique == 'Swordfish':
			return self.ScanXWingOrSwordfishOrJellyfish(3)
		elif technique == 'Y-Wing':
			return self.ScanYWingAndXYZWing(2)
		elif technique == 'XYZ-Wing':
			return self.ScanYWingAndXYZWing(3)
		elif technique == 'Bi-Value Universal Grave':
			return self.ScanBiValueUniversalGrave()
		elif technique == 'XY-Chain':
			return self.ScanXYChain()
		elif technique == 'X-Cycle':
			return self.ScanXCycle()
		elif technique == '3D Medusa Rule 1':
			return self.Scan3DMedusaRule1()
		elif technique == '3D Medusa Rule 2':
			return self.Scan3DMedusaRule2()
		elif technique == '3D Medusa Rule 3':
			return self.Scan3DMedusaRule3()
		elif technique == '3D Medusa Rule 4':
			return self.Scan3DMedusaRule4()
		elif technique == '3D Medusa Rule 5':
			return self.Scan3DMedusaRule5()
		elif technique == '3D Medusa Rule 6':
			return self.Scan3DMedusaRule6()
		elif technique == 'Jellyfish':
			return self.ScanXWingOrSwordfishOrJellyfish(4)
		elif technique == 'Unique Rectangle':
			return self.ScanUniqueRectangle()
		elif technique == 'WXYZ-Wing':
			return self.ScanWXYZWing()

		return False
	
	def CheckForConflicts(self):
		conflicting = False
		# Make sure that each solution appears only once per group
		for g in self.Puzzle.AllGroups:
			# Count the number of occurrances each solution has in the group by creating a dictionary for every solution associated with a list of cells that have the solution
			valueCells = dict([(i, set()) for i in range(1, 10)])
			for solution in range(1, 10):
				for cell in g.Cells:
					if cell.Solved and (cell.Value == solution):
						valueCells[solution].add(cell)
			
			# If any solution has more than one cell, those cells are in conflict
			for solution in valueCells:
				if len(valueCells[solution]) > 1:
					conflicting = True
					for cell in valueCells[solution]:
						cell.Conflicting = True
		
		# Make sure that no cell has zero candidates (even the solved cells)
		for cell in self.Puzzle.Cells:
			if cell.CandidateCount == 0:
				conflicting = True
				cell.Conflicting = True
		
		return conflicting
	
	def SolveNextStep(self, createSteps:bool=True):
		self.CreateSteps = (createSteps == True)
		
		self.Puzzle.ClearStepEliminatedCandidates()
		self.Puzzle.SinglesChains = None
		self.Puzzle.SuperChains = None

		# Try every technique (in order) to eliminate more candidates. Stop the step when progress is made (aka when any candidates are eliminated from any cells)
		madeProgress = False
		for technique in self.OrderedTechniques:
			if self.UseTechnique(technique):
				madeProgress = True
				break
		
		# If no progress has been made, stop
		if not madeProgress:
			return False

		# Apply the Sudoku rules
		self.ScanSudokuRules()

		# Check for conflicts
		if self.CheckForConflicts():
			return False

		return madeProgress
	
	def Solve(self, createSteps:bool=True):
		# Returns True if the Sudoku puzzle was completely solved, returns False if not

		# Start by using the Sudoku rules to eliminate candidates
		self.ScanSudokuRules()

		# Try taking steps until the puzzle is solved or no progress is made
		while True:
			if self.SolveNextStep(createSteps=createSteps):
				if self.Solved:
					self.Puzzle.CopyTo(self.SolvedPuzzle)
					return True
			else:
				return False
	
	def AddStep(self, techniqueData:SudokuTechniqueData):
		if not self.CreateSteps:
			return
		
		puzzle = self.Puzzle.Copy()
		
		# Re-target the techniqueData cell references to the copied puzzle in the step
		description = techniqueData.Description

		techniqueCells = set()
		for oldCell in techniqueData.TechniqueCells:
			for newCell in puzzle.Cells:
				if oldCell.Index == newCell.Index:
					techniqueCells.add(newCell)
		
		changedCells = set()
		for oldCell in techniqueData.ChangedCells:
			for newCell in puzzle.Cells:
				if oldCell.Index == newCell.Index:
					changedCells.add(newCell)
		
		techniqueCandidates = techniqueData.TechniqueCandidates.copy()

		techniqueData = SudokuTechniqueData(technique=techniqueData.Technique, techniqueCells=techniqueCells, changedCells=changedCells, techniqueCandidates=techniqueCandidates, description=description)
		
		step = SudokuStep(puzzle, techniqueData)

		self.Steps.append(step)
		return
	
	def ToStringConsole(self):
		origStr = self.OriginalPuzzle.ToStringConsole()
		finalStr = self.Puzzle.ToStringConsole()

		origLines = origStr.splitlines()
		finalLines = finalStr.splitlines()

		lineCount = len(origLines)

		lines = [None for i in range(lineCount)]
		separator = '  -->  '

		s = '       Original Puzzle:   ' + ' ' * len(separator)

		if self.Puzzle.Solved:
			s += '        Solved Puzzle:      '
		elif self.Puzzle.Conflicting:
			s += '      Conflicting Puzzle:   '
		else:
			s += '       Unsolved Puzzle:     '
		s += '\n'

		for i in range(lineCount):
			
			lines[i] = origLines[i]
			if i == 7:
				lines[i] += separator
			else:
				lines[i] += ' ' * len(separator)
			lines[i] += finalLines[i]
			s += lines[i] + '\n'
		
		return s

	def GetTranscript(self, includePuzzles:bool=False):
		s = ''
		solvedCount = -1
		for i, step in enumerate(self.Steps):
			s += 'Step ' + str(i) + ': ' + step.TechniqueData.Technique + '\n'
			if step.TechniqueData.Technique != 'Original':
				if len(step.TechniqueData.Description) > 0:
					s += step.TechniqueData.Description + '\n'
				s += step.TechniqueData.TechniqueCellsStr + '\n'
				s += step.TechniqueData.TechniqueCandidatesStr + '\n'
				s += step.TechniqueData.ChangedCellsStr + '\n'
				changesDescription = step.TechniqueData.ChangesDescription
				if changesDescription != 'No changes':
					s += step.TechniqueData.ChangesDescription + '\n'
				s += '\n'
			if includePuzzles:
				if step.Puzzle.SolvedCellsCount > solvedCount:
					s += step.Puzzle.ToStringConsole() + '\n'
					solvedCount = step.Puzzle.SolvedCellsCount
			
		s += 'Original Puzzle: ' + self.OriginalPuzzle.ToString(blankChar='0', newlines=False) + '\n'
		if self.Solved:
			s += 'Solved Puzzle:   '
		elif self.Puzzle.Conflicting:
			s += 'Conflicting Puzzle: '
		else:
			s += 'Unsolved Puzzle: '
		s += self.Puzzle.ToString(blankChar='0', newlines=False) + '\n'
		return s
	
	def GenerateSinglesChains(self):
		if self.Puzzle.SinglesChains is None:
			self.Puzzle.SinglesChains = SudokuSinglesChain.CreateAllSinglesChains(self.Puzzle)
		return
	
	def GenerateSuperChains(self):
		self.GenerateSinglesChains()
		if self.Puzzle.SuperChains is None:
			self.Puzzle.SuperChains = SudokuSuperChain.CreateSuperChains(self.Puzzle.SinglesChains)
		return




	''' Technique Methods '''
	def ScanSudokuRules(self):
		# Sudoku rules state that if a cell is solved, no other solved cell in the same row, column, or box may share the same vale as the original solved cell
		madeProgress = False

		# Scan for solved cells
		for solvedCell in self.Puzzle.Cells:
			if not solvedCell.Solved:
				continue

			# Cells that share a group with the solved cell that also have the solved cell's value as their candidate can eliminate that candidate
			for cell in solvedCell.SharedGroupCells:
				if cell.IsCandidate(solvedCell.Value):
					if cell.EliminateCandidate(solvedCell.Value):
						madeProgress = True
		
		return madeProgress
	
	def ScanNakedSingle(self):
		# A naked single is a cell with only one candidate remaining, which must be its solved value

		# Scan for unsolved cells with only one candidate
		for cell in self.Puzzle.Cells:
			if (not cell.Solved) and (cell.CandidateCount == 1):
				# Found a naked single
				candidate = list(cell.Candidates)[0]
				cell.SetValue(candidate)

				if self.CreateSteps:
					# Add step
					techniqueData = SudokuTechniqueData(technique='Naked Single', techniqueCells={cell}, changedCells={cell}, techniqueCandidates={candidate})
					techniqueData.Description = 'The only remaining candidate in cell ' + str(cell) + ' is ' + str(candidate) + ', which is its solution.'

					self.AddStep(techniqueData)
				return True
		return False

	def ScanHiddenSingle(self):
		# A hidden single occurs when a candidate appears only once in a group, making it the solution to the cell it appears in
		# Scan through every group
		for g in self.Puzzle.AllGroups:
			if g.Solved:
				continue

			# Count the number of occurrances each candidate has in the group by creating a dictionary for every candidate associated with a list of cells that have the candidate
			candidateCounts = dict([(i, set()) for i in range(1, 10)])
			for candidate in range(1, 10):
				for cell in g.Cells:
					if cell.IsCandidate(candidate):
						candidateCounts[candidate].add(cell)
			
			# If any candidate has only one cell which possesses it, it is a hidden single
			for candidate in range(1, 10):
				if len(candidateCounts[candidate]) != 1:
					continue

				# This is a hidden single
				cell = list(candidateCounts[candidate])[0]
				cell.SetValue(candidate)
				
				if self.CreateSteps:
					# Add step
					techniqueData = SudokuTechniqueData(technique='Hidden Single', techniqueCells={cell}, changedCells={cell}, techniqueCandidates={candidate})
					techniqueData.Description = g.ID + ' contains candidate ' + str(candidate) + ' only in cell ' + str(cell) + ', which is the cell\'s solution.'

					self.AddStep(techniqueData)
				return True
		return False
	
	def ScanPointingCombo(self, pointingCombo:int):
		# A pointing pair/triple occurs if a candidate occurs in only two/three cells in one group AND all of those cells share a different group in common
		if pointingCombo not in [2, 3]:
			return False

		# Scan through every group
		for g in self.Puzzle.AllGroups:
			if g.Solved:
				continue

			# Count the number of occurrances each candidate has in the group by creating a dictionary for every candidate associated with a list of cells that have the candidate
			candidateCounts = dict([(i, set()) for i in range(1, 10)])
			for candidate in range(1, 10):
				for cell in g.Cells:
					if cell.IsCandidate(candidate):
						candidateCounts[candidate].add(cell)
			
			# If the candidate occurs exactly pointingCombo times, the first criterion is met
			for candidate in range(1, 10):
				if len(candidateCounts[candidate]) != pointingCombo:
					continue
				
				# Do the cells all share at least one other group in common?
				cells = candidateCounts[candidate]
				groups = list(cells)[0].Groups
				for cell in cells:
					groups = groups.intersection(cell.Groups)
				groups.discard(g)

				if len(groups) < 1:
					continue

				# Found a pointing pair/triple
				for removalGroup in groups:
					madeProgress = False
					changedCells = set()

					for cell in removalGroup.Cells:
						if g in cell.Groups:
							continue
						
						if cell.EliminateCandidate(candidate):
							changedCells.add(cell)
							madeProgress = True

					# Add step
					if madeProgress:
						if self.CreateSteps:
							# Add step
							technique = 'Pointing Pair'
							if pointingCombo == 3:
								technique = 'Pointing Triplet'
							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates={candidate})

							numStr = 'two'
							if pointingCombo == 3:
								numStr = 'three'
							techniqueData.Description = g.ID + ' contains ' + numStr + ' instances of the candidate ' + str(candidate) + ' which all occur in ' + removalGroup.ID + ', allowing the candidate to be eliminated from all cells in ' + removalGroup.ID + ' that are not in ' + g.ID + '.'

							self.AddStep(techniqueData)
						return True
		return False
	
	def ScanNakedCombo(self, nakedCombo:int):
		# A Naked combo occurs when nakedCombo number of cells in a group have between 2 and nakedCombo candidates, and the number of candidates in the union of those candidates is equal to nakedCombo. Thus, the candidates may be removed from all other cells in the group
		if not (2 <= nakedCombo <= 5):
			return False
		
		# Scan through every group
		for g in self.Puzzle.AllGroups:
			if g.Solved:
				continue

			# Get all cells with the proper number of candidates
			validCells = set()
			for cell in g.Cells:
				if 2 <= cell.CandidateCount <= nakedCombo:
					validCells.add(cell)
			
			if len(validCells) < nakedCombo:
				continue
			
			# Get all combinations with the proper number of cells from validCells
			for cells in combinations(validCells, nakedCombo):
				# Get the union of all candidates in the cells
				candidates = set()
				for cell in cells:
					candidates = candidates.union(cell.Candidates)
				
				if len(candidates) != nakedCombo:
					continue
					
				# Found a naked combo
				madeProgress = False
				changedCells = set()

				for cell in g.Cells:
					if cell in cells:
						continue

					if cell.EliminateCandidates(candidates):
						changedCells.add(cell)
						madeProgress = True
				
				# Add step
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = 'Naked '
						if nakedCombo == 2:
							technique += 'Pair'
						elif nakedCombo == 3:
							technique += 'Triplet'
						elif nakedCombo == 4:
							technique += 'Quad'
						elif nakedCombo == 5:
							technique += 'Quint'
						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=candidates)

						techniqueData.Description = 'Cells ' + SudokuTechniqueData.ListToString(cells) + ' in ' + g.ID + ' contain only candidates ' + SudokuTechniqueData.ListToString(candidates) + ', allowing the candidates to be eliminated from the other cells in ' + g.ID + '.'

						self.AddStep(techniqueData)
					return True
		return False
	
	def ScanHiddenCombo(self, hiddenCombo:int):
		# A hidden combo occurs when a total of hiddenCombo number of some set of candidates occur only in hiddenCombo number of cells in a group where each of the cells contains two or more of the candidates. Thus, any other candidates can be eliminated from the cells.
		if not (2 <= hiddenCombo <= 4):
			return False
		
		# Scan through every group
		for g in self.Puzzle.AllGroups:
			if g.Solved:
				continue
			
			# Count the number of occurrances each candidate has in the group by creating a dictionary for every candidate associated with a list of cells that have the candidate
			candidateCounts = dict([(i, set()) for i in range(1, 10)])
			for candidate in range(1, 10):
				for cell in g.Cells:
					if cell.IsCandidate(candidate):
						candidateCounts[candidate].add(cell)
			
			# Get all unsolved candidates in the group
			unsolvedCandidates = set()
			for cell in g.Cells:
				if cell.CandidateCount < 2:
					continue
				unsolvedCandidates = unsolvedCandidates.union(cell.Candidates)
			
			# Get all combinations with the proper number of candidates from unsolvedCandidates
			for candidates in combinations(unsolvedCandidates, hiddenCombo):
				candidates = set(candidates)
				
				# Get all cells that contain any of the candidates
				cells = set()
				for candidate in candidates:
					cells = cells.union(candidateCounts[candidate])
				
				# Must have exactly hiddenCombo number of cells
				if len(cells) != hiddenCombo:
					continue
					
				# Each cell must contain two or more of the candidates, and all candidates must be represented throughout the cells
				cellsCandidates = set()
				skip = False
				for cell in cells:
					cellsCandidates = cellsCandidates.union(cell.Candidates)
					if len(cell.Candidates.intersection(candidates)) < 2:
						skip = True
						break
				if skip:
					continue
				if len(cellsCandidates.intersection(candidates)) != hiddenCombo:
					continue

				# Found a hidden combo
				madeProgress = False
				changedCells = set()

				for cell in cells:
					if cell.EliminateCandidates(cell.Candidates.difference(candidates)):
						changedCells.add(cell)
						madeProgress = True
				
				# Add step
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = 'Hidden '
						if hiddenCombo == 2:
							technique += 'Pair'
						elif hiddenCombo == 3:
							technique += 'Triplet'
						elif hiddenCombo == 4:
							technique += 'Quad'
						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=candidates)

						techniqueData.Description = 'Candidates ' + SudokuTechniqueData.ListToString(candidates) + ' occur only in cells ' + SudokuTechniqueData.ListToString(cells) + ' within ' + g.ID + ', allowing all other candidates in the cells to be eliminated.'

						self.AddStep(techniqueData)
					return True
		return False
	
	def ScanXWingOrSwordfishOrJellyfish(self, numGroups:int):
		# An X-Wing, Swordfish, or Jellyfish (numGroups = 2, 3, or 4 respectively) occurs when numGroups rows (or columns) 
		if numGroups not in [2, 3, 4]:
			return False
		
		# Scan through every combination of numGroups rows or columns
		for likeGroups in [self.Puzzle.Rows, self.Puzzle.Columns]:
			for groups in combinations(likeGroups, numGroups):
				skip = False
				for g in groups:
					if g.Solved:
						skip = True
						break
				if skip:
					continue

				# Cycle through each candidate
				for candidate in range(1, 10):
					skip = False

					# Cycle through each group in the combination and get all cells with the candidate. Reject the candidate if any groups do not have between [2, numGroups] cells with the candidate in it.
					cells = set()
					for g in groups:
						count = 0
						for cell in g.Cells:
							if cell.CandidateCount < 2:
								continue
							if candidate in cell.Candidates:
								cells.add(cell)
								count += 1
						if not (2 <= count <= numGroups):
							skip = True
							break
					if skip:
						continue
				
					# Get a set of all intersecting groups for the cells that are not in groups and are not boxes
					thisGroupType = list(groups)[0].Type
					intersectingGroups = set()
					for cell in cells:
						for g in cell.Groups:
							if (g.Type != SudokuGroupType.Box) and (g.Type != thisGroupType):
								intersectingGroups.add(g)
					
					# The number of intersecting groups must be numGroups
					if len(intersectingGroups) != numGroups:
						continue

					# Found an X-Wing/Swordfish/Jellyfish
					madeProgress = False
					changedCells = set()

					# Eliminate the candidate from the intersecting groups not in cells
					for intGroup in intersectingGroups:
						for cell in intGroup.Cells:
							if cell in cells:
								continue
							if cell.EliminateCandidate(candidate):
								madeProgress = True
								changedCells.add(cell)
					
					if madeProgress:
						if self.CreateSteps:
							# Add step
							technique = None
							if numGroups == 2:
								technique = 'X-Wing'
							elif numGroups == 3:
								technique = 'Swordfish'
							elif numGroups == 4:
								technique = 'Jellyfish'
							
							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates={candidate})

							techniqueData.Description = 'Candidate ' + str(candidate) + ' occurs '
							if numGroups == 2:
								techniqueData.Description += 'exactly two '
							else:
								techniqueData.Description += 'between two and '
								if numGroups == 3:
									techniqueData.Description += 'three '
								else:
									techniqueData.Description += 'four '
							techniqueData.Description += 'times each in ' + SudokuTechniqueData.ListToString(groups) + ' with cells ' + SudokuTechniqueData.ListToString(cells) + ' and also intersect ' + SudokuTechniqueData.ListToString(intersectingGroups) + ', which allows the candidate to be eliminated in the other cells in the intersecting groups.'

							self.AddStep(techniqueData)
						return True
		return False
	
	def ScanSinglesChainRule2(self):
		# Singles Chain Rule 2 occurs when two cells of the same color in a singles chain appear in the same group (a contradiction), which means the singles chain candidate can be eliminated from ALL cells in the chain of that color
		self.GenerateSinglesChains()

		# Cycle through all the singles chain
		for chain in self.Puzzle.SinglesChains:
			for colorNum in range(2):
				color = chain.Colors[colorNum]
				# Count the occurrence of each group in the color
				groupsCount = Counter()
				for cell in color:
					for group in cell.Groups:
						groupsCount[group] += 1

				# Check if any group appears more than once
				madeProgress = False
				changedCells = set()
				violatingGroups = set([group for group in groupsCount if groupsCount[group] > 1])

				if len(violatingGroups) > 0:
					# Found a least one instance of Singles Chain Rule 2
					# Eliminate the candidate from all cells of the color
					for cell in color:
						if cell.EliminateCandidate(chain.Candidate):
							madeProgress = True
							changedCells.add(cell)
					
					# The candidate is the solution for all cells of the other color
					solutionColor = (colorNum + 1) % 2
					for cell in chain.Colors[solutionColor]:
						cell.EliminateCandidates(cell.Candidates.difference({chain.Candidate}))
						cell.SetValue(chain.Candidate)
						madeProgress = True
						changedCells.add(cell)
						
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = 'Singles Chain Rule 2'

						violatingCells = set().union(*[group.Cells for group in violatingGroups]).intersection(color)

						description = 'Singles chain using candidate ' + str(chain.Candidate) + ' formed by links ' + SudokuTechniqueData.ListToString(chain.LinksToColorizedStringList()) + '. '
						
						description += 'Rule 2: Twice in a group. The chain singles contains multiple cells of the same color ' + SudokuTechniqueData.ListToString(violatingCells) + ' within ' + SudokuTechniqueData.ListToString(violatingGroups) + ', meaning that the other color is the solution to all cells in the singles chain that contain it.'

						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=chain.Cells, changedCells=changedCells, techniqueCandidates={chain.Candidate}, description=description)

						self.ScanSudokuRules()	# Do this because you solved cells
						self.AddStep(techniqueData)
					return True
		return False
	
	def ScanSinglesChainRule4(self):
		# Singles Chain Rule 4 occurs when a cell shares a group with two cells in a singles chain of different colors, which allows the singles chain candiate to be eliminated from the original cell
		self.GenerateSinglesChains()

		# Cycle through all singles chains
		for chain in self.Puzzle.SinglesChains:
			madeProgress = False
			changedCells = set()
			description = ''

			# Cycle through all pairs of different colored cells in the chain
			for cell1 in chain.Colors[0]:
				for cell2 in chain.Colors[1]:
					# Try to eliminate the singles chain candidate from all cells that intersect the two cells
					for cell in cell1.SharedGroupCells.intersection(cell2.SharedGroupCells):
						if cell.CandidateCount <= 1:
							continue
						if cell.EliminateCandidate(chain.Candidate):
							madeProgress = True
							if self.CreateSteps:
								changedCells.add(cell)
								description += ' Cell ' + str(cell) + ' intersects with two cells in the singles chain of different colors ' + SudokuTechniqueData.ListToString([cell1, cell2]) + ', allowing the singles chain candidate ' + str(chain.Candidate) + ' to be eliminated from the cell.'
			
			if madeProgress:
				if self.CreateSteps:
					# Add step
					technique = 'Singles Chain Rule 4'

					description = 'Singles chain using candidate ' + str(chain.Candidate) + ' formed by links ' + SudokuTechniqueData.ListToString(chain.LinksToColorizedStringList()) + '. Rule 4: Two colors elsewhere.' + description

					techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=chain.Cells, changedCells=changedCells, techniqueCandidates={chain.Candidate}, description=description)

					self.AddStep(techniqueData)
				return True
		return False
	
	def ScanYWingAndXYZWing(self, numLinkCandidates:int):
		# A Y-Wing/XYZ-Wing occurs when numLinkCandidates (2 and 3 respectively) appear in a link cell that intersects with two other wing cells that: do not intersect with each other, have exactly two candidates, each share a different candidate with the link cell, and share a candidate (the "wing" candidate) with each other that is not shared with the link cell for Y-Wings (numLinkCandidates == 2) but is shared with the link cell for XYZ-Wings (numLinkCandidates == 3). In the case of the Y-Wing, the wing candidate can be eliminated from any cell that intersects with both wing cells (except the link cell). In the case of the XYZ-Wing, the wing candidate can be eliminated from any cell that intersects with both wing cells and the link cell.
		if not (2 <= numLinkCandidates <= 3):
			return False
		
		# Scan through each cell
		for link in self.Puzzle.Cells:
			# Only accept link cells with the proper number of candidates
			if link.CandidateCount != numLinkCandidates:
				continue

			# Scan through all possible wing cells
			for wing1, wing2 in combinations(link.SharedGroupCells, 2):
				# Wings must have exactly two candidates each
				if (wing1.CandidateCount != 2) or (wing2.CandidateCount != 2):
					continue

				# Wings must not intersect
				if len(wing1.Groups.intersection(wing2.Groups)) > 0:
					continue

				# Wings must each share a candidate with the link cell that is not in the other wing cell
				if wing1.Candidates == wing2.Candidates:
					continue
				if len(wing1.Candidates.intersection(link.Candidates)) != (numLinkCandidates - 1):
					continue
				if len(wing2.Candidates.intersection(link.Candidates)) != (numLinkCandidates - 1):
					continue

				# Wings must share one "wing" candidate with each other (and the link cell only for XYZ-Wings)
				wingsSharedCandidates = wing1.Candidates.intersection(wing2.Candidates)
				if len(wingsSharedCandidates) != 1:
					continue
				wingCandidate = list(wingsSharedCandidates)[0]

				if numLinkCandidates == 2:
					# For Y-Wing only
					if wingCandidate in link.Candidates:
						continue
				else:
					# For XYZ-Wing only
					if wingCandidate not in link.Candidates:
						continue
				
				# Found a Y-Wing/XYZ-Wing
				madeProgress = False
				changedCells = set()

				# Potential cells to eliminate the wing candidate from must intersect both wing cells and cannot be the wing cells or the link cell. For XYZ-Wings, they must also intersect the link cell
				intersectingCells = wing1.SharedGroupCells.intersection(wing2.SharedGroupCells)
				intersectingCells.discard(link)
				if numLinkCandidates == 3:
					intersectingCells = intersectingCells.intersection(link.SharedGroupCells)
				
				# Try to eliminate the cells
				for cell in intersectingCells:
					if cell.CandidateCount <= 1:
						continue
					if cell.EliminateCandidate(wingCandidate):
						madeProgress = True
						changedCells.add(cell)
				
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = None

						if numLinkCandidates == 2:
							technique = 'Y-Wing'
						else:
							technique = 'XYZ-Wing'
						
						description = 'Link cell ' + str(link) + ' '
						if numLinkCandidates == 3:
							description += 'contains wing candidate ' + str(wingCandidate) + ' along with two other candidates'
						else:
							description += 'contains two candidates'
						description += ' and intersects wing cells ' + SudokuTechniqueData.ListToString([wing1, wing2]) + ' which: have two candidates, do not intersect with one another, share a candidate with the link cell but not each other, and share the wing candidate ' + str(wingCandidate) + ' with each other '
						if numLinkCandidates == 2:
							description += 'but not the link cell'
						description += ', which allows the wing candidate to be eliminated from any other cells that intersect with the wing cells'
						if numLinkCandidates == 3:
							description += ' and the link cell'
						description += '.'

						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=set([link, wing1, wing2]), changedCells=changedCells, techniqueCandidates={wingCandidate}, description=description)

						self.AddStep(techniqueData)
					return True
		return False
	
	def ScanWXYZWing(self):
		# A WXYZ-Wing occurs when four cells (each with between 2 to 4 candidates) contain a union of 4 candidates, and exactly one of those candidates is a non-restricted common digit, while the others are restricted digits. A restricted digit is a candidate where each cell (from the four cells) that contains it intersects with all other cells that contain it (from the four cells). A non-restricted common digit is a candidate that is not a restricted digit. The non-restricted common digit can be eliminated from all cells that intersect with every cell in the WXYZ-Wing that contains the non-restricted common digit.
		
		# Evidently, WXYZ wings only occur if all four cells are selected from the union of one row or column and one box.
		for box in self.Puzzle.Boxes:
			for rowcol in self.Puzzle.Rows + self.Puzzle.Columns:
				# Get a set of all cells in the box and row/col with 2 to 4 candidates
				possibleCells = set([cell for cell in box.Cells.union(rowcol.Cells) if (2 <= cell.CandidateCount <= 4)])

				# Cycle through all combinations of four cells in the possible cells
				for cells in combinations(possibleCells, 4):
					# Get the union of all candidates for the cells
					candidates = set()
					for cell in cells:
						candidates.update(cell.Candidates)
					
					if len(candidates) != 4:
						continue

					# Make a dictionary for each candidate containing the set of cells that contain each one
					candidateCells = dict([(candidate, set([cell for cell in cells if candidate in cell.Candidates])) for candidate in candidates])
					
					# Find the non-restricted common digit, if there is one. Stop if there is more than one
					skip = False
					nrcd = None
					for candidate in candidateCells:
						# The candidate cannot appear only once
						if len(candidateCells[candidate]) < 2:
							skip = True
							break

						# If each cell with the candidate intersects all cells with the candidate, it is not an NRCD
						for cell1, cell2 in combinations(candidateCells[candidate], 2):
							if not (cell1 in cell2.SharedGroupCells):
								# This is an NRCD
								if (nrcd is not None) and (candidate != nrcd):
									# There cannot be more than one NRCD
									skip = True
									break
								nrcd = candidate
								continue
						if skip:
							break
					if skip:
						continue
					if nrcd is None:
						continue

					# Found a WXYZ-Wing and non-restricted common digit
					madeProgress = False
					changedCells = set()

					# Eliminate the NRCD from all cells that intersect the WXYZ-Wing cells with the NRCD that are not in the 
					intersectingCells = set.intersection(*[cell.SharedGroupCells for cell in cells if nrcd in cell.Candidates])
					
					for cell in intersectingCells:
						if cell.CandidateCount <= 1:
							continue
						if cell.EliminateCandidate(nrcd):
							madeProgress = True
							changedCells.add(cell)

					if madeProgress:
						if self.CreateSteps:
							# Add step
							technique = 'WXYZ-Wing'
							description = 'The four cells ' + SudokuTechniqueData.ListToString(cells) + ' together contain the four candidates ' + SudokuTechniqueData.ListToString(candidates) + ', of which only candidate ' + str(nrcd) + ' is a non-restricted common digit, which allows it to be eliminated from all other cells that intersect the aformentioned cells that also contain it.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=candidates, description=description)

							self.AddStep(techniqueData)
						return True
		return False
	
	def ScanBiValueUniversalGrave(self):
		# A Bi-Value Universal Grave (BUG) occurs when all unsolved cells have exactly two candidates remaining except one, which has exactly three. In this circumstance, the candidate which, if removed, would make all remaining candidates in each intersecting group occur exactly twice is the solution to the cell.

		# Scan the puzzle to see if all unsolved cells have two candidates except for one that has three (the BUG cell)
		bugCell = None
		for cell in self.Puzzle.Cells:
			if cell.CandidateCount > 3:
				return False
			if cell.CandidateCount == 3:
				if bugCell is not None:
					return False
				bugCell = cell
		
		if bugCell is None:
			return False
		
		# Determine the candidate that occurs exactly three times in each group intersecting the BUG cell
		for candidate in bugCell.Candidates:
			skip = False
			for group in bugCell.Groups:
				count = 0
				for cell in group.Cells:
					if cell.IsCandidate(candidate):
						count += 1
				if count != 3:
					skip = True
					break
			if skip:
				continue

			# This is the BUG candidate, the solution to the cell
			bugCell.SetValue(candidate)

			if self.CreateSteps:
				technique = 'Bi-Value Universal Grave'
				techniqueCells = set()
				techniqueCells.add(bugCell)
				for cell in self.Puzzle.Cells:
					if cell.CandidateCount >= 2:
						techniqueCells.add(cell)
				description = 'All unsolved cells have exactly two candidates except the BUG cell ' + str(bugCell) + ', which has three. Candidate ' + str(candidate) + ' is the solution to the BUG cell because if it were eliminated, all remaining cells would have exactly two candidates, which is impossible.'

				techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=techniqueCells, changedCells={bugCell}, techniqueCandidates={candidate}, description=description)

				self.AddStep(techniqueData)
			return True
		return False
	
	def Scan3DMedusaRule1(self):
		# 3D Medusa Rule 1 occurs when a cell contains two or more candidates of the same color in a super chain. Consequently, all candidates with that color in the super chain can be eliminated.
		self.GenerateSuperChains()

		# Scan through every super chain
		for superChain in self.Puzzle.SuperChains:
			# Scan through every cell in the super chain
			for cell in superChain.Cells:
				# Scan through both colors
				for colorNum in range(2):
					count = 0
					# Scan through the color in every singles chain
					for singlesChain in superChain.SinglesChains:
						if cell in singlesChain.Colors[colorNum]:
							count += 1
						if count >= 2:
							# Found a 3D Medusa Rule 1
							madeProgress = False
							changedCells = set()

							## Eliminate all candidates of the color from every cell in the #super chain
							#for sc in superChain.SinglesChains:
							#	for c in sc.Colors[colorNum]:
							#		if c.CandidateCount <= 1:
							#			continue
							#		if c.EliminateCandidate(sc.Candidate):
							#			madeProgress = True
							#			changedCells.add(c)

							# The opposite color is the solution for all cells that contain it
							solutionColor = (colorNum + 1) % 2
							for sc in superChain.SinglesChains:
								for c in sc.Colors[solutionColor]:
									c.EliminateCandidates(c.Candidates.difference({sc.Candidate}))
									c.SetValue(sc.Candidate)
									madeProgress = True
									changedCells.add(c)
							
							if madeProgress:
								if self.CreateSteps:
									# Add step
									technique = '3D Medusa Rule 1'
									description = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '. '

									description += 'Rule 1: Twice in a Cell. Cell ' + str(cell) + ' contains two candidates with the same color (' + {0: 'Red', 1: 'Blue'}[colorNum] + '), meaning that the other color is the solution to all cells in the super chain that contain it.'

									techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells=changedCells, techniqueCandidates=superChain.Candidates, description=description)
									
									self.ScanSudokuRules()	# Do this because you solved cells
									self.AddStep(techniqueData)
								return True
		return False
	
	def Scan3DMedusaRule2(self):
		# 3D Medusa Rule 2 occurs when a group contains two cells in a super chain that both have the same candidate in the same color. Consequently, the opposite color is the solution to all cells that contain it.
		self.GenerateSuperChains()

		# Cycle through all super chains
		for superChain in self.Puzzle.SuperChains:
			# Cycle through all candidates
			for candidate in superChain.Candidates:
				# Cycle through both colors
				for colorNum in range(2):
					# Get all cells in the super group with the candidate colored with the color
					coloredCandidateCells = set().union(*[singlesChain.Colors[colorNum] for singlesChain in superChain.SinglesChains if singlesChain.Candidate == candidate])

					# Cycle through all groups
					for group in self.Puzzle.AllGroups:
						sameColorCells = group.Cells.intersection(coloredCandidateCells)
						if len(sameColorCells) >= 2:
							# Found a Rule 2
							madeProgress = False
							changedCells = set()

							# The opposite color is the solution for all cells that contain it
							solutionColor = (colorNum + 1) % 2
							for singlesChain in superChain.SinglesChains:
								for cell in singlesChain.Colors[solutionColor]:
									cell.EliminateCandidates(cell.Candidates.difference({singlesChain.Candidate}))
									cell.SetValue(singlesChain.Candidate)
									madeProgress = True
									changedCells.add(cell)

							if madeProgress:
								if self.CreateSteps:
									# Add step
									technique = '3D Medusa Rule 2'

									description = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '. '

									description += 'Rule 2: Twice in a group. ' + str(group) + ' contains the cells ' + SudokuTechniqueData.ListToString(sameColorCells) + ' that both contain candiate ' + str(candidate) + ' of the same color (' + {0: 'Red', 1: 'Blue'}[colorNum] + '), meaning that the other color is the solution to all cells in the super chain that contain it.'

									techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells=changedCells, techniqueCandidates=superChain.Candidates, description=description)

									self.ScanSudokuRules()	# Do this because you solved cells
									self.AddStep(techniqueData)
								return True
		return False

	def Scan3DMedusaRule3(self):
		# 3D Medusa Rule 3 occurs when a cell in a super chain contains both colors in its candidates. Consequently, any uncolored candidates in the cell can be eliminated
		self.GenerateSuperChains()
		
		# Cycle through all super chains
		for superChain in self.Puzzle.SuperChains:
			# Choose a cell with three or more candidates
			for cell in [cell for cell in superChain.Cells if cell.CandidateCount >= 3]:
				# Determine if the cell has both colors
				coloredCandidates = set()
				hasColor = [False, False]
				for singlesChain in superChain.SinglesChains:
					for colorNum in range(2):
						if cell in singlesChain.Colors[colorNum]:
							coloredCandidates.add(singlesChain.Candidate)
							hasColor[colorNum] = True
				if all(hasColor):
					# Found a 3D Medusa Rule 3
					if cell.EliminateCandidates(cell.Candidates.difference(coloredCandidates)):
						if self.CreateSteps:
							# Add step
							technique = '3D Medusa Rule 3'

							description = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '. '

							description += 'Rule 3: Two colors in a cell. Cell ' + str(cell) + ' contains both colors in its candidates ' + SudokuTechniqueData.ListToString(coloredCandidates) + ', allowing all other candidates in the cell to be eliminated.'
							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells={cell}, techniqueCandidates=superChain.Candidates, description=description)

							self.AddStep(techniqueData)
						return True
		return False

	def Scan3DMedusaRule4(self):
		# 3D Medusa Rule 4 is very similar to Singles Chain Rule 4. It occurs occurs when a cell shares a group with two cells in a super chain, both of which contain the same candidate belonging to one of the singles chains in the super chain but of different colors, which allows the candiate to be eliminated from the original cell
		self.GenerateSuperChains()

		# Scan through the super chains
		for superChain in self.Puzzle.SuperChains:
			# Cycle through each candidate
			for candidate in range(1, 10):
				madeProgress = False
				changedCells = set()
				description = ''

				# Get all cells that contain the candidate (only if it is colored) in the super chain
				coloredCandidateCells = [set(), set()]
				for singlesChain in [singlesChain for singlesChain in superChain.SinglesChains if singlesChain.Candidate == candidate]:
					coloredCandidateCells[0].update(singlesChain.Colors[0])
					coloredCandidateCells[1].update(singlesChain.Colors[1])

				# Get every combination of the candidate cells of different colors
				for cell1 in coloredCandidateCells[0]:
					for cell2 in coloredCandidateCells[1]:
						# Eliminate the candidate from all cells that intersect with the two colored candidate cells
						for cell in [cell for cell in cell1.SharedGroupCells.intersection(cell2.SharedGroupCells) if cell not in superChain.Cells]:
							if cell.CandidateCount <= 1:
								continue
							if cell.EliminateCandidate(candidate):
								madeProgress = True
								if self.CreateSteps:
									changedCells.add(cell)
									description += ' Cell ' + str(cell) + ' intersects with the cells in the super chain ' + SudokuTechniqueData.ListToString([cell1, cell2]) + ' containing candidate ' + str(candidate) + ' but with different colors, allowing the candidate to be eliminated from the cell.'
				
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = '3D Medusa Rule 4'

						prefix = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '.'

						prefix += 'Rule 4: Two colors elsewhere.'
						description = prefix + description

						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells=changedCells, techniqueCandidates=superChain.Candidates, description=description)

						self.AddStep(techniqueData)
					return True
		return False
	
	def Scan3DMedusaRule5(self):
		# 3D Medusa Rule 5 occurs when a cell within a super chain: contains an uncolored candidate, intersects with another cell containing the candidate but the candidate is colored, and contains any opposite colored candidate within the cell. In this case, the uncolored candidate can be eliminated from the cell.
		self.GenerateSuperChains()

		# Cycle through all the super chains
		for superChain in self.Puzzle.SuperChains:
			madeProgress = False
			changedCells = set()
			description = ''

			# Cycle through each cell in the super chain
			for cell in superChain.Cells:
				if cell.CandidateCount <= 1:
					continue
				# Determine the colored candidate(s) in the cell
				insideColoredCandidates = [None, None]
				for singlesChain in [singlesChain for singlesChain in superChain.SinglesChains if singlesChain.Candidate in cell.Candidates]:
					if cell in singlesChain.Colors[0]:
						insideColoredCandidates[0] = singlesChain.Candidate
					elif cell in singlesChain.Colors[1]:
						insideColoredCandidates[1] = singlesChain.Candidate
				if not any(insideColoredCandidates):
					# This rule doesn't work if there is not one colored candidate in the cell
					continue
				if all(insideColoredCandidates):
					# This rule doesn't work if both colors are in the cell, but Rule 1 could work for it
					continue
				
				# Get the inside colored candidate the color number of the outside candidate
				insideColoredCandidate = insideColoredCandidates[0]
				outsideColorNum = 1
				if insideColoredCandidate is None:
					insideColoredCandidate = insideColoredCandidates[1]
					outsideColorNum = 0
				
				# Cycle through the remaining uncolored candidates in the cell
				for candidate in cell.Candidates.difference({insideColoredCandidate}):
					# Search for an intersecting cell with the opposite color
					outsideCells = cell.SharedGroupCells.intersection(set().union(*[singlesChain.Colors[outsideColorNum] for singlesChain in superChain.SinglesChains if candidate == singlesChain.Candidate]))
					if len(outsideCells) > 0:
						# Found a Rule 5
						
						# Eliminate the candidate from the cell
						if cell.EliminateCandidate(candidate):
							madeProgress = True
							if self.CreateSteps:
								changedCells.add(cell)
								description += ' Cell ' + str(cell) + ' contains uncolored candidate ' + str(candidate) + ', contains colored, arbitrary candidate ' + str(insideColoredCandidate) + ', and intersects with ' + str(list(outsideCells)[0]) + ' which contains the candidate with the opposite color, allowing the uncolored candidate to be eliminated from the cell.'

			if madeProgress:
				if self.CreateSteps:
					# Add step
					technique = '3D Medusa Rule 5'

					prefix = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '.'

					prefix += 'Rule 5: Two colors in cell and group.'
					description = prefix + description

					techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells=changedCells, techniqueCandidates=superChain.Candidates, description=description)

					self.AddStep(techniqueData)
				return True
		return False
	
	def Scan3DMedusaRule6(self):
		# 3D Medusa Rule 6 occurs when a cell outside a super chain intersect with cells in the super chain that, in union, have all of the candidates in the cell colorized by a single color. Consequently, the other color represents the solutions to all the cells that contain it.
		self.GenerateSuperChains()

		# Cycle through all super chains
		for superChain in self.Puzzle.SuperChains:
			# Cycle through all unsolved cells outside the super chain
			for cell in [cell for cell in set(self.Puzzle.Cells).difference(superChain.Cells) if cell.CandidateCount >= 2]:
				# Cycle through both colors
				for colorNum in range(2):
					allCandidatesHaveColor = True
					# Cycle through all candidates in the cell
					for candidate in cell.Candidates:
						# Get all cells in the super chain that contain the candidate of the desired color
						cellsWithColoredCandidate = set().union(*[singlesChain.Colors[colorNum] for singlesChain in superChain.SinglesChains if singlesChain.Candidate == candidate])

						if len(cell.SharedGroupCells.intersection(cellsWithColoredCandidate)) == 0:
							allCandidatesHaveColor = False
							break
					if not allCandidatesHaveColor:
						continue

					# Found a 3D Medusa Rule 6
					madeProgress = False
					changedCells = set()

					# The opposite color is the solution for all cells that contain it
					solutionColor = (colorNum + 1) % 2
					for singlesChain in superChain.SinglesChains:
						for cell in singlesChain.Colors[solutionColor]:
							cell.EliminateCandidates(cell.Candidates.difference({singlesChain.Candidate}))
							cell.SetValue(singlesChain.Candidate)
							madeProgress = True
							changedCells.add(cell)
					
					if madeProgress:
						if self.CreateSteps:
							# Add step
							technique = '3D Medusa Rule 6'

							description = 'Super chain formed by singles chains ' + superChain.ChainToString() + ' with bi-candidate link cells ' + SudokuTechniqueData.ListToString(superChain.LinkCells) + '. '

							description += 'Rule 6: Cell emptied by color. All candidates in cell ' + str(cell) + ' intersect with like-candidate cells that all share the same color (' + {0: 'Red', 1: 'Blue'}[colorNum] + ') in the super chain, meaning that the other color is the solution to all cells in the super chain that contain it.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=superChain.Cells, changedCells=changedCells, techniqueCandidates=superChain.Candidates, description=description)

							self.ScanSudokuRules()	# Do this because you solved cells
							self.AddStep(techniqueData)
						return True
		return False
	
	'''
	def ScanXCycle(self):
		self.GenerateNiceLoops()
		
		# Cycle through all nice loops
		for niceLoop in self.Puzzle.NiceLoops:
			if niceLoop.Rule == 1:
				# The nice loop generator rejects loops with more than one pair of back-to-back weak links. Because of this, if the loop has an even number of cells, then it must alternate between weak and strong links between every link. Note that a strong link can become a weak link if both ends are back-to-back with proper strong links.

				# Any cells that intersect with both cells in a weak link (and are not in the nice loop) can have the nice loop candidate eliminated.
				madeProgress = False
				changedCells = set()

				for weakLinkCell1, weakLinkCell2 in [list(weakLink) for weakLink in niceLoop.WeakLinks]:
					for cell in [cell for cell in weakLinkCell1.SharedGroupCells.intersection(weakLinkCell2.SharedGroupCells).difference(niceLoop.Cells) if cell.CandidateCount >= 2]:
						if cell.EliminateCandidate(niceLoop.Candidate):
							madeProgress = True
							changedCells.add(cell)
				
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = 'X-Cycle'
						
						description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

						description += 'X-Cycle Rule 1: The nice loop created with candidate ' + str(niceLoop.Candidate) + ' alternates between strong and weak links, therefore the cell'
						if len(changedCells) > 1:
							description += 's'
						description += ' ' + SudokuTechniqueData.ListToString(changedCells) + ' containing the candidate and intersecting with two cells in the nice loop can have the candidate eliminated.'

						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells=changedCells, techniqueCandidates={niceLoop.Candidate}, description=description)
						
						self.AddStep(techniqueData)
					return True
			elif niceLoop.Rule == 2:
				# Find the cell that has two strong links connected to it
				for i in range(len(niceLoop.StrongWeakPattern)):
					if (niceLoop.StrongWeakPattern[i] == 1) and (niceLoop.StrongWeakPattern[i - 1] == 1):
						# Found back-to-back strong links. Get the cell in between
						cell = niceLoop.Chain[i]

						# The nice loop candidate is the solution to the cell
						cell.EliminateCandidates(cell.Candidates.difference({niceLoop.Candidate}))
						cell.SetValue(niceLoop.Candidate)

						if self.CreateSteps:
							technique = 'X-Cycle'

							description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

							description += 'X-Cycle Rule 2: Cell ' + str(cell) + ' is connected to two strong links, meaning the nice loop candidate ' + str(niceLoop.Candidate) + ' is its solution.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells={cell}, techniqueCandidates={niceLoop.Candidate}, description=description)

							self.ScanSudokuRules()	# Do this because you solved cells
							self.AddStep(techniqueData)
						return True
			elif niceLoop.Rule == 3:
				# Find the cell that has two weak links connected to it
				for i in range(len(niceLoop.StrongWeakPattern)):
					if (niceLoop.StrongWeakPattern[i] == 0) and (niceLoop.StrongWeakPattern[i - 1] == 0):
						# Found back-to-back weak links. Get the cell in between
						cell = niceLoop.Chain[i]

						# The nice loop candidate can be eliminated from the cell
						cell.EliminateCandidate(niceLoop.Candidate)

						if self.CreateSteps:
							technique = 'X-Cycle'

							description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

							description += 'X-Cycle Rule 3: Cell ' + str(cell) + ' is connected to two weak links, allowing the nice loop candidate ' + str(niceLoop.Candidate) + ' to be eliminated from the cell.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells={cell}, techniqueCandidates={niceLoop.Candidate}, description=description)

							self.AddStep(techniqueData)
						return True
		return False
	'''
	
	def ScanXCycle(self):
		self.GenerateSinglesChains()

		# Cycle through each candidate to make nice loops with
		for candidate in range(1, 10):
			# Find all strong and weak links for this candidate
			
			# All possible strong links are the links of all the singles chains for the candidate
			allStrongLinks = []
			cellsWithStrongLinks = set()
			for singlesChain in [sc for sc in self.Puzzle.SinglesChains if sc.Candidate == candidate]:
				for link in singlesChain.Links:
					allStrongLinks.append(link)
					cellsWithStrongLinks = cellsWithStrongLinks.union(link)
			
			if len(allStrongLinks) == 0:
				continue

			allCandidateCells = set([cell for cell in self.Puzzle.Cells if cell.IsCandidate(candidate)])

			# Build a chain up until it forms a nice loop or it quits
			# Every nice loop must start (and end) with a strong link. Cycle through every strong link as a starting point
			for startingStrongLink in allStrongLinks:
				chain = [cell for cell in startingStrongLink]
				
				if self.recursiveNiceLoopExaminer(candidate, allCandidateCells, allStrongLinks, chain, 0):
					return True

				chain = [chain[1], chain[0]]

				if self.recursiveNiceLoopExaminer(candidate, allCandidateCells, allStrongLinks, chain, 0):
					return True
		return False
	
	def recursiveNiceLoopExaminer(self, candidate:int, allCandidateCells:set, allStrongLinks:list, chain:list, backToBackWeakLinksCount:int):
		# If the last two links are weak links, add to the back-to-back weak links count
		if len(chain) >= 3:
			link = {chain[-1], chain[-2]}
			if link not in allStrongLinks:
				link = {chain[-2], chain[-3]}
				if link not in allStrongLinks:
					backToBackWeakLinksCount += 1
		
		# There cannot be more than two back-to-back weak links in the chain
		if backToBackWeakLinksCount >= 2:
			return False
		
		# If the end cell is the same as the beginning cell, the chain is closed and complete
		if chain[-1] == chain[0]:
			# A chain must contain at least four cells (plus one, because the end cell appears twice)
			if len(chain) < 5:
				return False
			
			# Found a nice loop
			# This loop is guaranteed to contain at least one strong link, but is not guaranteed to have any more.
			
			# Determine if each link is strong or weak
			cells = set(chain)
			
			strongLinks = []
			weakLinks = []
			pattern = []
			hasBackToBackWeakLinks = False
			seriesWeakLinks = 0
			rule = 1
			for i in range(len(chain) - 1):
				cell1 = chain[i]
				cell2 = chain[i + 1]
				link = {cell1, cell2}
				if link in allStrongLinks:
					strongLinks.append(link)
					pattern.append(1)
					seriesWeakLinks = 0
				else:
					weakLinks.append(link)
					pattern.append(0)
					seriesWeakLinks += 1
					if seriesWeakLinks == 2:
						if hasBackToBackWeakLinks:
							# More than one set of back-to-back weak links
							return False
						if (len(cells) % 2) != 1:
							# A nice loop with back-to-back weak links must have an odd number of cells
							return False
						hasBackToBackWeakLinks = True
					elif seriesWeakLinks >= 3:
						return False
			if len(weakLinks) == 0:
				# A nice loop needs at least one weak link. If it has none, then a pointing pair would have already solved it
				return False
			if (len(cells) % 2) == 0:
				# A nice loop with an even number of cells must alternate between strong and weak links
				for i in range(len(pattern)):
					if ((i % 2) == 0):
						if  (pattern[i] == 0):
							return False
					else:
						pattern[i] = 0
			else:
				# A nice loop with an odd number of cells must alternate between strong and weak links except for in one place, where it is allowed to have back-to-back strong links or back-to-back weak links
				if hasBackToBackWeakLinks:
					rule = 3
					# Find the index of the second weak link in the back-to-back weak links
					for i in range(1, len(pattern)):
						if (pattern[i] == 0) and (pattern[i - 1]) == 0:
							# Make sure the loop alternates between strong and weak links starting at i
							for j in range(len(pattern)):
								if ((j % 2) == 1):
									if (pattern[(i + j) % len(pattern)] == 0):
										return False
								else:
									pattern[(i + j) % len(pattern)] = 0
							break
				else:
					rule = 2
					# Find the index of the last strong link in a series of strong links that is even in number
					backToBackStrongLinksCount = 0
					for i in range(len(pattern) * 2):
						if pattern[i % len(pattern)] == 1:
							backToBackStrongLinksCount += 1
						else:
							if (backToBackStrongLinksCount % 2) == 0:
								# Found the index of the last strong link in a series of strong links that is even in number
								index = (i - 1) % len(pattern)
								for j in range(len(pattern)):
									if ((j % 2) == 0):
										if(pattern[(index + j) % len(pattern)]) == 0:
											return False
									else:
										pattern[(index + j) % len(pattern)] = 0
								break
							backToBackStrongLinksCount = 0

			# Create the SudokuNiceLoop object and append it to allNiceLoops in-place
			niceLoop = SudokuNiceLoop()

			niceLoop.Candidate = candidate
			niceLoop.Rule = rule
			niceLoop.Chain = chain
			niceLoop.StrongWeakPattern = pattern
			niceLoop.StrongLinks = strongLinks
			niceLoop.WeakLinks = weakLinks
			niceLoop.Cells = cells

			# Check the nice loop for any X-Cycle patterns
			if niceLoop.Rule == 1:
				# The nice loop generator rejects loops with more than one pair of back-to-back weak links. Because of this, if the loop has an even number of cells, then it must alternate between weak and strong links between every link. Note that a strong link can become a weak link if both ends are back-to-back with proper strong links.

				# Any cells that intersect with both cells in a weak link (and are not in the nice loop) can have the nice loop candidate eliminated.
				madeProgress = False
				changedCells = set()

				for weakLinkCell1, weakLinkCell2 in [list(weakLink) for weakLink in niceLoop.WeakLinks]:
					for cell in [cell for cell in weakLinkCell1.SharedGroupCells.intersection(weakLinkCell2.SharedGroupCells).difference(niceLoop.Cells) if cell.CandidateCount >= 2]:
						if cell.EliminateCandidate(niceLoop.Candidate):
							madeProgress = True
							changedCells.add(cell)
				
				if madeProgress:
					if self.CreateSteps:
						# Add step
						technique = 'X-Cycle'
						
						description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

						description += 'X-Cycle Rule 1: The nice loop created with candidate ' + str(niceLoop.Candidate) + ' alternates between strong and weak links, therefore the cell'
						if len(changedCells) > 1:
							description += 's'
						description += ' ' + SudokuTechniqueData.ListToString(changedCells) + ' containing the candidate and intersecting with two cells in the nice loop can have the candidate eliminated.'

						techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells=changedCells, techniqueCandidates={niceLoop.Candidate}, description=description)
						
						self.AddStep(techniqueData)
					return True
			
			elif niceLoop.Rule == 2:
				# Find the cell that has two strong links connected to it
				for i in range(len(niceLoop.StrongWeakPattern)):
					if (niceLoop.StrongWeakPattern[i] == 1) and (niceLoop.StrongWeakPattern[i - 1] == 1):
						# Found back-to-back strong links. Get the cell in between
						cell = niceLoop.Chain[i]

						# The nice loop candidate is the solution to the cell
						cell.EliminateCandidates(cell.Candidates.difference({niceLoop.Candidate}))
						cell.SetValue(niceLoop.Candidate)

						if self.CreateSteps:
							technique = 'X-Cycle'

							description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

							description += 'X-Cycle Rule 2: Cell ' + str(cell) + ' is connected to two strong links, meaning the nice loop candidate ' + str(niceLoop.Candidate) + ' is its solution.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells={cell}, techniqueCandidates={niceLoop.Candidate}, description=description)

							self.ScanSudokuRules()	# Do this because you solved cells
							self.AddStep(techniqueData)
						return True
			elif niceLoop.Rule == 3:
				# Find the cell that has two weak links connected to it
				for i in range(len(niceLoop.StrongWeakPattern)):
					if (niceLoop.StrongWeakPattern[i] == 0) and (niceLoop.StrongWeakPattern[i - 1] == 0):
						# Found back-to-back weak links. Get the cell in between
						cell = niceLoop.Chain[i]

						# The nice loop candidate can be eliminated from the cell
						cell.EliminateCandidate(niceLoop.Candidate)

						if self.CreateSteps:
							technique = 'X-Cycle'

							description = 'Nice loop on cells ' + niceLoop.ChainToString() + '. '

							description += 'X-Cycle Rule 3: Cell ' + str(cell) + ' is connected to two weak links, allowing the nice loop candidate ' + str(niceLoop.Candidate) + ' to be eliminated from the cell.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=niceLoop.Cells, changedCells={cell}, techniqueCandidates={niceLoop.Candidate}, description=description)

							self.AddStep(techniqueData)
						return True
		
		# The chain is currently incomplete. Cycle through each new cell from the allCells set that is not already part of the chain and that intersects with the current end cell but not with the current second to last cell
		for cell in [c for c in allCandidateCells.intersection(chain[-1].SharedGroupCells).difference(chain[-2].SharedGroupCells) if c not in chain[1:]]:
			# Add the next end cell to the end of the chain and call the next recursion
			if self.recursiveNiceLoopExaminer(candidate, allCandidateCells, allStrongLinks, chain + [cell], backToBackWeakLinksCount):
				return True
		return False

	def ScanXYChain(self):
		# An XY-Chain occurs when the endpoints of a chain of bi-value cells contain at least one candidate in common, in which case any cells that intersect with the endpoints can have the common endpoint candidates removed.

		# Get all bi-value cells
		biValueCells = set([cell for cell in self.Puzzle.Cells if cell.CandidateCount == 2])

		# Start the chain with a single bi-value cell
		for startCell in biValueCells:
			chain = [startCell]

			# Start the search with each candiate in the bi-value cell
			for unconnectedCandidate in startCell.Candidates:
				linkCandidate = list(startCell.Candidates.difference({unconnectedCandidate}))[0]
				if self.recursiveXYChainExaminer(biValueCells, unconnectedCandidate, linkCandidate, chain):
					return True
		return False
	
	def recursiveXYChainExaminer(self, biValueCells:set, unconnectedCandidate:int, linkCandidate:int, chain:list):
		# Is the chain complete? Criteria: chain length >= 2, endpoints contain the unconnected candidate
		if (len(chain) >= 2) and (linkCandidate == unconnectedCandidate):
			# Found an XY-Chain
			madeProgress = False
			changedCells = set()
			description = ''

			# Eliminate the candidate from all cells that contain the unconnected candidate that intersect with both endpoints
			for cell in [cell for cell in chain[-1].SharedGroupCells.intersection(chain[0].SharedGroupCells) if cell.IsCandidate(unconnectedCandidate) and (cell not in chain)]:
				if cell.EliminateCandidate(unconnectedCandidate):
					madeProgress = True
					if self.CreateSteps:
						changedCells.add(cell)
						description += ' Cell ' + str(cell) + ' intersects with both ends of the XY-Chain and contains the unconnected end candidate, allowing the candidate to be eliminated from the cell.'
			
			if madeProgress:
				if self.CreateSteps:
					technique = 'XY-Chain'

					chainStr = ''
					for cell in chain:
						chainStr += str(cell) + '-'

					description = 'XY-Chain using unconnected end candidate ' + str(unconnectedCandidate) + ' found in cells ' + chainStr[:-1] + '.' + description
					
					techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=set(chain), changedCells=changedCells, techniqueCandidates={unconnectedCandidate}, description=description)

					self.AddStep(techniqueData)
				return True
		
		# Add another link to the chain that: is not already part of the chain, contains the link candidate
		for cell in [cell for cell in chain[-1].SharedGroupCells.intersection(biValueCells) if (cell not in chain) and (cell.IsCandidate(linkCandidate))]:
			# Get the new link candidate, the other candidate in the cell besides the old link candidate
			newLinkCandidate = list(cell.Candidates.difference({linkCandidate}))[0]
			
			# Build the chain with the new cell and scan the chain
			if self.recursiveXYChainExaminer(biValueCells, unconnectedCandidate, newLinkCandidate, chain + [cell]):
				return True
		return False
	
	def ScanUniqueRectangle(self):
		# A unique rectangle occurs when: four unsolved cells reside in exactly two rows, two columns, and two boxes; at least one cell contains exactly two candidates; and all cells contain the candidates in the two candidate cell(s).
		
		# Get four cells in two rows, two columns, and two boxes
		for row1, row2 in combinations(self.Puzzle.Rows, 2):
			# Are the rows in the same line of boxes?
			rowsSameBox = (row1.Index // 3) == (row2.Index // 3)

			for col1, col2 in combinations(self.Puzzle.Columns, 2):
				# Are the columns in the same line of boxex?
				colsSameBox = (col1.Index // 3) == (col2.Index // 3)

				# Either the rows or columns must be in the same line of boxes, but not both nor none
				if rowsSameBox == colsSameBox:
					continue
				
				# Get the cells
				cells = (row1.Cells & col1.Cells) | (row1.Cells & col2.Cells) | (row2.Cells & col1.Cells) | (row2.Cells & col2.Cells)

				# At least one cell must have exactly two candidates (the UR candidates). All cells with exactly two candidates must share the same set of two candidates.
				urCandidates = None
				biValueCells = set()
				skip = False
				for cell in cells:
					if cell.CandidateCount  < 2:
						skip = True
						break
					elif cell.CandidateCount == 2:
						if urCandidates is not None:
							if cell.Candidates != urCandidates:
								skip = True
								break
						urCandidates = cell.Candidates
						biValueCells.add(cell)
				if skip:
					continue
				if urCandidates is None:
					continue
					
				# All cells must contain the UR candidates
				for cell in cells:
					if not urCandidates.issubset(cell.Candidates):
						skip = True
						break
				if skip:
					continue

				if len(biValueCells) == 4:
					# This is a non-unique Sudoku puzzle
					continue
				
				# Found a Unique Rectangle
				madeProgress = False
				changedCells = set()
				
				# Scan for Rule 1
				# Rule 1 occurs when there are exactly three bi-value cells, and allows the last cell to have the UR candidates eliminated from it.
				if len(biValueCells) == 3:
					# The only non-bi-value cell can have the UR candidates removed
					for cell in [cell for cell in cells if cell.CandidateCount >= 3]:
						if cell.EliminateCandidates(urCandidates):
							madeProgress = True
							changedCells.add(cell)
					
					if madeProgress:
						if self.CreateSteps:
							# Add step
							technique = 'Unique Rectangle'

							description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. '

							description += 'Rule 1: Cell ' + str(list(changedCells)[0]) + ' is the only cell in the unique rectangle contains more than two candidates, allowing the unique rectangle candidates to be eliminated from the cell.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=urCandidates, description=description)

							self.AddStep(techniqueData)
						return True
				
				# Scan for Rule 2
				# Rule 2 occurs when there are exactly two bi-value cells and the remaining two cells each have three candidates which are exactly the same. Conseqently, any cell that intersects with both non-bi-value cells can have the non-UR candidate eliminated
				if len(biValueCells) == 2:
					nonBiValueCells = list(cells.difference(biValueCells))
					if (nonBiValueCells[0].CandidateCount == 3) and (nonBiValueCells[0].Candidates == nonBiValueCells[1].Candidates):
						# Found a Rule 2
						madeProgress = False
						changedCells = set()

						# Eliminate the off-candidate from the intersecting cells
						candidate = list(nonBiValueCells[0].Candidates.difference(urCandidates))[0]

						for cell in [cell for cell in nonBiValueCells[0].SharedGroupCells.intersection(nonBiValueCells[1].SharedGroupCells) if cell.CandidateCount >= 2]:
							if cell.EliminateCandidate(candidate):
								madeProgress = True
								changedCells.add(cell)
						
						if madeProgress:
							if self.CreateSteps:
								# Add step
								technique = 'Unique Rectangle'

								description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. '

								description += 'Rule 2: Cells ' + SudokuTechniqueData.ListToString(nonBiValueCells) + ' contain only the same three candidates, allowing the candidate ' + str(candidate) + ' not present in the bi-value cells to be eliminated from any cell that intersects the non-bi-value cells.'

								techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=urCandidates, description=description)

								self.AddStep(techniqueData)
							return True
				
				# Scan for Rule 3
				if len(biValueCells) == 2:
					# Get the non-bi-value cells
					nonBiValueCells = list(cells.difference(biValueCells))
					
					# Get the union of the candidates in the non-bi-value cells (not including the UR candidates), aka the unshared candidates
					candidates = nonBiValueCells[0].Candidates.union(nonBiValueCells[1].Candidates).difference(urCandidates)

					# Check if the non-bi-value cells have exactly three candidates each, two of which belong to the UR candidates and another that is NOT shared between the non-bi-value cells
					if (nonBiValueCells[0].CandidateCount == 3) and (nonBiValueCells[1].CandidateCount == 3) and (len(candidates) == 2):
						madeProgress = False
						changedCells = set()
						description = ''

						# Cycle through each group that intersects with the two non-bi-value cells
						for g in nonBiValueCells[0].Groups.intersection(nonBiValueCells[1].Groups):
							# Search for a bi-value cell containing the unshared candidates that is NOT in the UR
							for lockCell in [cell for cell in g.Cells if (cell not in cells) and (cell.Candidates == candidates)]:
								# Found a Rule 3
								# Eliminate the candidates from all cells in the group except the UR cells and the lock cell
								for cell in [cell for cell in g.Cells.difference(cells).difference({lockCell}) if cell.CandidateCount >= 2]:
									if cell.EliminateCandidates(candidates):
										madeProgress = True
										if self.CreateSteps:
											changedCells.add(cell)
											description += ' Cell ' + str(lockCell) + ' contains only the unshared candidates, allowing the unshared candidates to be removed along ' + str(g) + ' in ' + SudokuTechniqueData.ListToString(changedCells) + '.'
								
						if madeProgress:
							if self.CreateSteps:
								# Add step
								technique = 'Unique Rectangle'

								description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. Rule 3: Cells ' + SudokuTechniqueData.ListToString(nonBiValueCells) + ' each contain only three candidates: both the unique rectangle candidates and one of two unshared candidates ' + SudokuTechniqueData.ListToString(candidates) + '.' + description

								techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=urCandidates, description=description)

								self.AddStep(techniqueData)
							return True
					
					elif len(candidates) == 2:
						# Look for triple pseudo-cells
						madeProgress = False
						changedCells = set()
						description = ''
						allNonBiValueCellCandidates = nonBiValueCells[0].Candidates.union(nonBiValueCells[1].Candidates)

						# Cycle through each group that intersects with the two non-bi-value cells
						for g in nonBiValueCells[0].Groups.intersection(nonBiValueCells[1].Groups):
							# Get all cells in the group that: contain one or both unshared candidates, contain exactly one other non-unshared candidate, contain no UR candidates
							lockCells = set([cell for cell in g.Cells if (cell not in cells) and (len(cell.Candidates.intersection(candidates)) >= 1) and (len(cell.Candidates.difference(allNonBiValueCellCandidates)) == 1) and (len(cell.Candidates.intersection(urCandidates)) == 0)])

							# Must have 2 or more lock cells
							if len(lockCells) <= 1:
								continue
							
							# All unshared candidates must make at least one appearance in the locked cells
							lCells = list(lockCells)
							if not candidates.issubset(lCells[0].Candidates.union(lCells[0].Candidates)):
								continue

							# Lock cells must contain the same "other non-unshared candidate"
							if len(lCells[0].Candidates.intersection(lCells[1].Candidates).difference(candidates)) != 1:
								continue

							# Found a Rule 3 with Triple Pseudo-Cells
							# Eliminate the candidates from all cells in the group except the UR cells and the lock cells
							for cell in [cell for cell in g.Cells.difference(cells).difference(lockCells) if cell.CandidateCount >= 2]:
								if cell.EliminateCandidates(candidates):
									madeProgress = True
									if self.CreateSteps:
										changedCells.add(cell)
										description += ' Cells ' + SudokuTechniqueData.ListToString(lockCells) + ' contain only the unmatched candidates and one other candidate that does not appear in the unique rectangle cells, allowing the unmatched candidates to be removed along ' + str(g) + ' in ' + SudokuTechniqueData.ListToString(changedCells) + '.'
						if madeProgress:
							if self.CreateSteps:
								# Add step
								technique = 'Unique Rectangle'

								description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. Rule 3 with Triple Pseudo-Cells: Cells ' + SudokuTechniqueData.ListToString(nonBiValueCells) + ' each contain only three candidates: both the unique rectangle candidates and one of two unmatched candidates ' + SudokuTechniqueData.ListToString(candidates) + '.' + description

								techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=changedCells, techniqueCandidates=urCandidates, description=description)

								self.AddStep(techniqueData)
							return True
				
				# Scan for Rule 4
				# Rule 4 occurs when one of the UR candidates occurs only in the non-bi-value cells within their shared group(s). In that case, the other UR candidate can be eliminated from the non-bi-value cells.
				if len(biValueCells) == 2:
					# Get the non-bi-value cells
					nonBiValueCells = list(cells.difference(biValueCells))

					# Cycle through each group that intersects with the two non-bi-value cells
					for g in nonBiValueCells[0].Groups.intersection(nonBiValueCells[1].Groups):
						for twiceCandidate in urCandidates:
							if sum([1 for cell in g.Cells if cell.IsCandidate(twiceCandidate)]) == 2:
								# Found a Rule 4
								candidate = list(urCandidates.difference({twiceCandidate}))[0]
								
								# Remove the other candidate from the non-bi-value cells
								for cell in nonBiValueCells:
									cell.EliminateCandidate(candidate)
								
								if self.CreateSteps:
									technique = 'Unique Rectangle'

									description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. '

									description += 'Rule 4: Unique rectangle candidate ' + str(twiceCandidate) + ' in the non-bi-value cells ' + SudokuTechniqueData.ListToString(nonBiValueCells) + ' occurs only twice in ' + str(g) + ', allowing the other unique rectangle candidate ' + str(candidate) + ' to be eliminated from the non-bi-value cells.'

									techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells=nonBiValueCells, techniqueCandidates=urCandidates, description=description)

									self.AddStep(techniqueData)
								return True
				
				# Scan for Hidden Unique Rectangle Rule 1
				if len(biValueCells) == 1:
					# Get the cell in the opposite corner of the 
					biValueCell = list(biValueCells)[0]
					oppositeCell = [cell for cell in cells if (cell not in biValueCell.SharedGroupCells) and (cell != biValueCell)][0]

					# Cycle through the UR candidates
					for strongLinkCandidate in urCandidates:
						# A strong link must be present in the opposite cell's row and column using the candidate
						if sum(1 for cell in oppositeCell.Row.Cells if cell.IsCandidate(strongLinkCandidate)) != 2:
							continue
						if sum(1 for cell in oppositeCell.Column.Cells if cell.IsCandidate(strongLinkCandidate)) != 2:
							continue

						# Found a Hidden Unique Rectangle Rule 1
						# Get the opposite candidate
						candidate = list(urCandidates.difference({strongLinkCandidate}))[0]
						oppositeCell.EliminateCandidate(candidate)

						if self.CreateSteps:
							technique = 'Unique Rectangle'

							description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. '

							description += 'Hidden Unique Rectangle Rule 1: Cell ' + str(oppositeCell) + ' contains a strong link for unique rectangle candidate ' + str(strongLinkCandidate) + ' in both ' + str(oppositeCell.Row) + ' and ' + str(oppositeCell.Column) + ', allowing the other unique rectangle candidate ' + str(candidate) + ' to be eliminated from the cell.'

							techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells={oppositeCell}, techniqueCandidates=urCandidates, description=description)

							self.AddStep(techniqueData)
						return True
				
				# Scan for Hidden Unique Rectangle Rule 2
				if len(biValueCells) == 2:
					nonBiValueCells = cells.difference(biValueCells)

					# If any bi-value cell contains a strong link with a non-bi-value cell, it's a Rule 2
					for biValueCell in biValueCells:
						for nonBiValueCell in nonBiValueCells:
							if len(biValueCell.Groups.intersection(nonBiValueCell.Groups)) > 0:
								continue

							for g in biValueCell.Groups.intersection(nonBiValueCell.Groups):
								for strongLinkCandidate in urCandidates:
									if sum(1 for cell in g.Cells if cell.IsCandidate(strongLinkCandidate)) != 2:
										continue

									# Found a Hidden Unique Rectangle Rule 2
									cell = list(nonBiValueCells.difference({nonBiValueCell}))[0]
									candidate = list(urCandidates.difference({strongLinkCandidate}))[0]

									if cell.EliminateCandidate(candidate):
										if self.CreateSteps:
											technique = 'Unique Rectangle'

											description = 'Unique Rectangle using candidates ' + SudokuTechniqueData.ListToString(urCandidates) + ' on cells ' + SudokuTechniqueData.ListToString(cells) + '. '

											description += 'Hidden Unique Rectangle Rule 2: Candidate ' + str(strongLinkCandidate) + ' forms a strong link between bi-value cell ' + str(biValueCell) + ' and non-bi-value cell ' + str(nonBiValueCell) + ', allowing the other unique rectangle candidate ' + str(candidate) + ' to be eliminated from the other non-bi-value cell ' + str(cell) + '.'

											techniqueData = SudokuTechniqueData(technique=technique, techniqueCells=cells, changedCells={cell}, techniqueCandidates=urCandidates, description=description)

											self.AddStep(techniqueData)
										return True
		return False

if __name__ == "__main__":
	# Get the arguments
	parser = argparse.ArgumentParser()
	
	parser.add_argument(
		'--input',
		'-i',
		type=str,
		default=None,
		help='The input Sudoku file')
	
	parser.add_argument(
		'--output',
		'-o',
		type=str,
		default=None,
		help='The output Sudoku file. The solver will fill in as many of the blank cells from the input as it can.')
	
	parser.add_argument(
		'--sudokuString',
		'-s',
		type=str,
		default=None,
		help='The sudoku string, passed in via command line. The string is required to be exactly 81 characters long')
	
	parser.add_argument(
		'--transcriptFile',
		type=str,
		default=None,
		help='The output file to save the solver transcript')
	
	parser.add_argument(
		'--printTranscript',
		default=False,
		action='store_true',
		help='Prints the transcript of the solver')
	
	args = parser.parse_args()
	
	# Load the puzzle
	solver = SudokuSolver()
	if args.input is not None:
		solver.Setup(puzzlePath=args.input)
	elif args.sudokuString is not None:
		solver.Setup(puzzleString=args.sudokuString)
	else:
		print('To input the sudoku puzzle into the solver, please provide either the --input or the --sudokuString arguments')
		parser.print_help()
		exit(-1)
	
	# Solve the puzzle
	solver.Solve()
	
	# Print the transcript (if desired)
	if args.printTranscript:
		print(solver.GetTranscript(includePuzzles=False))
	
	# Print or save the solved output file
	if args.output is None:
		print(solver.ToStringConsole())
	else:
		with open(args.output, 'w') as f:
			f.write(solver.SolvedPuzzle.ToString(blankChar='.', newlines=False))
	
	# Save the transcript (if desired)
	if args.transcriptFile is not None:
		with open(args.transcriptFile, 'w') as f:
			f.write(solver.GetTranscript(includePuzzles=True))
