"""UIRoot, the widget at the top of a UI's widget tree.

A UIRoot fills its UI's area (the whole screen by default) instead of anchoring
to a parent, so every widget added to the UI is positioned relative to it. It
never has a parent itself: giving it one raises an error.
"""
