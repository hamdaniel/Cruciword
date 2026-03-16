from __future__ import annotations
from abc import ABC


class Cell(ABC):
	"""Abstract base class for all board cells."""
	pass


class ClueCell(Cell):
	"""Represents a clue cell."""

	def __str__(self):
		return "?"


class RunStart:
	"""
	Represents the start of a run.
	origin: direction of the clue cell relative to the start cell
	length: length of the run
	"""

	def __init__(self, origin, length):
		self.origin = origin
		self.length = length

	def __repr__(self):
		return f"RunStart(origin={self.origin}, length={self.length})"


class LetterCell(Cell):
	"""
	Represents a letter cell.
	It may start a horizontal run, a vertical run, both, or neither.
	"""

	def __init__(self):
		self.horizontal_run = None
		self.vertical_run = None

	def has_horizontal_start(self):
		return self.horizontal_run is not None

	def has_vertical_start(self):
		return self.vertical_run is not None

	def has_any_start(self):
		return self.has_horizontal_start() or self.has_vertical_start()

	def clear_vertical(self):
		self.vertical_run = None
		
	def clear_horizontal(self):
		self.horizontal_run = None

	def __str__(self):
		parts = []

		if self.horizontal_run:
			parts.append(f"{self.horizontal_run.origin}L{self.horizontal_run.length}")

		if self.vertical_run:
			parts.append(f"{self.vertical_run.origin}D{self.vertical_run.length}")

		return "|".join(parts) if parts else " "