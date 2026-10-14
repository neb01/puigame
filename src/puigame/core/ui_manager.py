"""UIManager, the object that runs one UI.

UIManager routes pygame events to widgets, tracks the highlighted widget and
any press in progress, and manages the mouse cursor. Games reach it through
``UI``, which passes the common calls through.
"""
