"""InteractiveWidget, the base class for widgets the user can interact with.

InteractiveWidget extends Widget with the ``highlightable`` flag, its
``highlightable_in_tree`` version, and the highlight and activation behaviour
that interactive widgets share. Button, Checkbox, and TextBox build on it.

It lives in ``core`` so that the UIManager can recognise interactive widgets
with ``isinstance()`` without importing from ``widgets``.
"""
