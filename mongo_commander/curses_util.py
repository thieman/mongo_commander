"""Apparently you can't monkey-patch Curses windows, so we've got to
have this stupid module instead."""

def movedown(window, rows, x):
    current_y, current_x = window.getyx()
    window.move(current_y+rows, x)
