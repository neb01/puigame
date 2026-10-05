"""Skins, which turn a size and a state into a widget surface.

A skin reads its rules from a theme: for example, a rectangle with a given
colour and corner radius, 50% dimmer when disabled, and 20% lighter with a
halo when highlighted. It can build surfaces of any size from these rules,
so one skin can serve many widgets, each asking for its own size.

DrawnSkin draws surfaces in code from the theme's colours and shapes.
ImageSkin loads an image file and scales it with nine-slice scaling.

Widgets cache the surfaces their skin produces, one per state, and swap
between them as their state changes.
"""
