"""UIRoot, the widget at the top of a UI's widget tree.

A UIRoot covers the surface its UI draws on, and the UI's top-level widgets,
created with ``ui.root`` as their parent, are positioned relative to it. It has
no parent, holds the theme that every widget in its tree draws with, and draws
nothing itself.
"""

import math

from pygame.typing import Point

from puigame._components.skin import NoSkin
from puigame._styling.theme import Theme
from puigame.core.widget import Widget


class UIRoot(Widget):
    """Widget at the top of a UI's tree, holding the tree's theme.

    A UIRoot has no parent and no appearance: it uses a ``NoSkin``, so its image
    is 0x0. Its rect covers the surface the UI draws on, at ``(0, 0)`` moved by
    its ``offset``, so changing the offset moves the whole UI, for example to
    shake it. It ignores its anchors and margin. The UI's top-level widgets
    anchor against it. ``UI`` creates it, so games rarely need to.
    """

    def __init__(
        self,
        *,
        size: Point,
        theme: Theme,
    ) -> None:
        """Create the root of a widget tree.

        Unlike other widgets, this does not call ``Widget.__init__()``, which
        needs a parent. It sets up the root and its theme first, so that the
        images can be built, then runs the setup shared with ``Widget``.

        Args:
            size: Width and height of the surface the UI draws on, in pixels.
            theme: Theme that every widget in the tree draws with.

        Raises:
            ValueError: If either dimension of ``size`` is negative.
        """
        # deliberately not calling Widget.__init__(), which needs a parent
        self._theme = theme
        self._parent = None
        self._root = self

        # a root ignores its anchors and margin, so it keeps the defaults, and it
        # never consumes clicks, so that clicks on empty space reach the game
        self._setup(size=size, skin=NoSkin(), consumes_clicks=False)

    @property
    def theme(self) -> Theme:
        """The theme that every widget in the tree draws with."""
        return self._theme

    def kill(self) -> None:
        """Raise an error, since the root of a tree cannot be killed.

        To remove a whole UI, drop every reference to it.

        Raises:
            TypeError: Always.
        """
        raise TypeError("kill() cannot be called on UIRoot")

    def _place_tree(self) -> None:
        """Place the root, then every widget below it, parents before children.

        This is the layout pass. It runs once per frame, before drawing, so
        that changes to any widget's offset, the root's included, take effect.
        Setting an offset moves nothing until the pass runs.
        """
        for widget in self._iter_subtree():
            widget._place()

    def _update_tree(self) -> None:
        """Refresh the image of the root and of every widget below it.

        Each widget shows the cached image and position for its current state.
        This runs once per frame, after the layout pass.
        """
        for widget in self._iter_subtree():
            widget._update()

    def _place(self) -> None:
        """Place the rect at ``(0, 0)`` moved by the offset.

        Overrides ``Widget._place()``, since the root has no parent to be placed
        against. The offset is rounded down on each axis, as for every other
        widget, so a fractional offset rounds the same way everywhere.
        """
        self.rect.topleft = (
            math.floor(self.offset.x),
            math.floor(self.offset.y),
        )
