"""Sprite group that draws the widget tree.

WidgetGroup extends pygame's LayeredUpdates (itself an extension of the
standard Group). It keeps layers in line with the widget hierarchy, so
children draw above their parents, skips widgets that are not visible,
and lets layering change while the game runs.
"""
