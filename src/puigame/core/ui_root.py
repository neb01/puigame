"""UIRoot, the widget at the top of a UI's widget tree.

A UIRoot fills its UI's area, and the UI's top-level widgets, created with
``ui.root`` as their parent, are positioned relative to it. It has no parent,
holds the theme that every widget in its tree draws with, and draws nothing
itself.
"""

from pygame.typing import Point

from puigame.components.skin import NoSkin
from puigame.core.widget import Widget
from puigame.themes.theme import Theme


class UIRoot(Widget):
    """Widget at the top of a UI's tree, holding the tree's theme.

    A UIRoot has no parent and no appearance: it uses a ``NoSkin``, so its image
    is empty. Its rect is placed directly from ``pos`` and ``size`` rather than
    by anchors, and the UI's top-level widgets anchor against it. ``UI``
    creates it, so games rarely need to.
    """

    def __init__(
        self,
        size: Point,
        pos: Point,
        theme: Theme,
    ) -> None:
        """Create the root of a widget tree.

        Unlike other widgets, this does not call ``Widget.__init__()``, which
        needs a parent. It sets up the root and its theme first, so that the
        images can be built, then runs the setup shared with ``Widget``.

        Args:
            size: Width and height of the UI's area in pixels.
            pos: ``(x, y)`` position of the area's top-left corner in pixels.
            theme: Theme that every widget in the tree draws with.

        Raises:
            ValueError: If either dimension of ``size`` is negative.
        """
        # deliberately not calling Widget.__init__(), which needs a parent
        self._theme = theme
        self._parent = None
        self._root = self

        self._setup(size, NoSkin())  # a root's anchors are unused: keep defaults

        self._rect.topleft = pos

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
