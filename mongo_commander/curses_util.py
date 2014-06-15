"""Apparently you can't monkey-patch Curses windows, so we've got to
have this stupid module instead."""

def movedown(window, rows=1, x=None):
    current_y, current_x = window.getyx()
    window.move(current_y+rows, x if x is not None else current_x)

def movex(window, new_x):
    current_y = window.getyx()[0]
    window.move(current_y, new_x)
