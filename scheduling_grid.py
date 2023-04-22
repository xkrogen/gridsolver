#!/usr/bin/env python3
import sys
import random
import time
from typing import List, Optional

import click
from tabulate import tabulate


# set up the command-line argument parsing using the 'click' library
@click.command()
@click.option('--size', default=12, show_default=True, help='Size of the grid.')
@click.option('--max-attempts', default=1_000_000, show_default=True, help='Maximum number of attempts to generate a valid grid.')
@click.option('--seed', default=None, show_default=True, help='Random seed to use when generating the grid.')
@click.argument('positions', nargs=-1)
def generate(size: int, seed: Optional[int], max_attempts: int, positions: List[str]):
    """
    Generate a <size>-by-<size> grid of numbers 1 through <size> such that each
    row and column contains each number exactly once.

    POSITIONS is a list of position values in the form row,col=value. These are used as initial, fixed values
    in the grid. Other values are randomly generated.

    \b
    For example:
      > ./scheduling_grid 1,1=1 3,4=5
    """
    # set a random seed if one was provided, otherwise use a randomly generated seed
    # this allows for the ability to reproduce the same grid by fixing the pseudo-randomness
    if seed:
        seed_internal = seed
    else:
        seed_internal = random.randint(0, sys.maxsize)
    print(f'Attempting to generate grid of size {size} with seed {seed_internal} ...')

    # create a list of lists to represent the grid
    # this is a matrix/2-dimensional array
    grid_initial = [[0 for _ in range(size)] for _ in range(size)]

    # measure the start time to track how long it takes to generate the grid
    start_time = time.time_ns()

    # populate initial values set in the grid by the command-line arguments
    for position in positions:
        # split the position into row,column and value
        rowcol, value = position.split('=')
        # split the row/column into separate values
        row, col = rowcol.split(',')
        # convert the value to an integer and validate that it's in the proper range
        ival = int(value)
        assert 0 < ival <= size, f'Invalid value {value} at position {row},{col}'
        # set the value at the given position in the grid matrix
        grid_initial[int(row) - 1][int(col) - 1] = ival

    # validate the initial grid, ensuring that there are no rows or columns with duplicate values
    # this is just validating that the user-provided input is good, or else it will be impossible
    # to generate a valid grid later
    for row_num, row in enumerate(grid_initial):
        assert len([v for v in row if v != 0]) == len(set(row) - {0}), f'Row {row_num} is invalid: ' + str(','.join([str(v) for v in row]))
    for col_num in range(size):
        col = [row[col_num] for row in grid_initial]
        assert len(set(col) - {0}) == len([v for v in col if v != 0]), f'Column {col_num} is invalid: ' + str(','.join([str(v) for v in col]))

    grid_final = None
    attempts = 0
    # create a pseudo-random number generator using the seed we generated earlier
    rand = random.Random(seed_internal)

    # The basic concept here is that we're going to try to generate a grid by randomly filling in the
    # empty cells with values that are valid for that row and column. This won't always work --
    # it's like trying to fill in a Sudoku grid by just starting to randomly fill in numbers that
    # don't conflict and hoping it works out. But if we try enough times, eventually we can
    # generate a valid grid this way. (There are smarter ways to do this, but they're more complicated,
    # and it's not necessary for a grid of this size. Brute force randomness works just fine.)
    while attempts < max_attempts:
        attempts += 1

        try:
            # create a copy of the grid to work on without messing up the initial grid
            grid = [row[:] for row in grid_initial]

            # iterate over the matrix by iterating over the rows/columns
            for row in grid:
                for col_num in range(size):
                    # if we encounter a cell that hasn't been filled yet ...
                    if row[col_num] == 0:
                        # find the set of numbers that could possibly fill that cell by subtracting out
                        # all of the numbers that already appear elsewhere in the same row/column
                        cell_candidates = set(range(1, size + 1)) - set(row) - {row[col_num] for row in grid}
                        # if we can't find a valid number, then we've hit a dead end and need to start over
                        if len(cell_candidates) == 0:
                            # this exits the loop and starts over with a different seed
                            raise ValueError(f'No candidates for seed {seed}')
                        # otherwise, randomly pick a number from the set of candidates and fill in the cell
                        row[col_num] = rand.choice(list(cell_candidates))
            # if we get here, then we've successfully generated a valid grid, so we can stop
            grid_final = grid
            break
        except ValueError:
            continue  # try again with a different seed

    if not grid_final:
        raise ValueError(f'No valid grid found after {max_attempts} attempts :(')

    # validate the grid one last time to make sure it's actually good and we didn't mess anything up
    for row_num, row in enumerate(grid_final):
        assert set(row) == set(range(1, size + 1)), f'Row {row_num} is invalid: ' + str(','.join([str(v) for v in row]))
    for col_num in range(size):
        col_vals = [row[col_num] for row in grid_final]
        assert set(col_vals) == set(range(1, size + 1)), f'Column {col_num} is invalid: ' + str(','.join([str(v) for v in col_vals]))

    end_time = time.time_ns()

    print(f'Generated valid grid in {(end_time - start_time) / 1_000_000} ms after {attempts} attempts.')

    # print the grid
    grid_with_row_nums = [[f'r{r}'] + [str(v) for v in row] for r, row in enumerate(grid_final, start=1)]
    print(tabulate(grid_with_row_nums, tablefmt='grid', headers=([''] + [f'c{c}' for c in range(1, size + 1)])))


if __name__ == '__main__':
    generate(sys.argv[1:])
