"""UI, the object a game uses to create and run a set of widgets.

A UI combines a UIRoot, the top of its widget tree, with a UIManager that runs
it: input routing, the highlight, press capture, and the cursor. It also owns
the theme and the WidgetGroup that draws the tree.

UI passes the common calls through, so a game rarely needs the root or the
manager directly: ``add()`` attaches a widget to the root, and
``handle_event()``, ``update()``, and ``draw()`` run the UI each frame. A
screen that shows several UIs at once, such as a pause menu over a HUD, uses a
separate UI for each, with the game deciding their order.
"""
