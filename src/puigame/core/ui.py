"""UI, the object a game uses to create and run a set of widgets.

A UI holds a UIRoot, the top of its widget tree, which holds the theme. It lays
out the tree and draws it, each widget above its parent. A top-level widget is
created with ``ui.root`` as its parent, and ``update()`` and ``draw()`` run the
UI each frame. A screen that shows several UIs at once, such as a pause menu
over a HUD, uses a separate UI for each, with the game deciding their order.
"""

import pygame as pg
from pygame.typing import Point

from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME, Theme

# one frame at 60 fps, for games that update once per fixed-rate frame
DEFAULT_DT = 1 / 60


class UI:
    """A widget tree, with its layout and drawing, run by the game each frame.

    The UI lays out and draws on a surface of the ``size`` given on creation,
    and its rects are in that surface's pixels. Each frame, the game calls
    ``update()``, then ``draw()``.
    """

    def __init__(
        self,
        *,
        size: Point,
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Create a UI and the root of its widget tree.

        Args:
            size: Width and height of the surface the UI draws on, in pixels.
                For a display opened with ``pg.SCALED``, this is the display's
                own size, not the window's.
            theme: Theme that every widget in the UI draws with.

        Raises:
            ValueError: If either dimension of ``size`` is negative.
        """
        self._root = UIRoot(size=size, theme=theme)

    @property
    def root(self) -> UIRoot:
        """The widget at the top of the UI's tree, the parent of top-level widgets.

        Set on creation and never changed, so it is read-only.
        """
        return self._root

    def update(self, dt: float = DEFAULT_DT) -> None:
        """Lay out the widgets and refresh their images for this frame.

        Call once per frame, after handling events and before ``draw()``.
        Changes made to widgets since the last update, such as a new offset or
        flag, take effect here: the layout pass places every widget against its
        parent, then each widget shows its image for its current state.

        Args:
            dt: Time since the last frame, in seconds. Defaults to
                ``DEFAULT_DT``, one frame at 60 fps. Games running at another
                or a variable frame rate pass the real elapsed time, for
                example ``clock.tick(fps) / 1000``.
        """
        self.root._place_tree()
        self.root._update_tree()

    def draw(self, surface: pg.Surface) -> None:
        """Draw the visible widgets onto ``surface``.

        Each widget is drawn, then its whole subtree, then its next sibling, so
        children appear above their parents and a later sibling's subtree above
        an earlier one's. A hidden widget is skipped along with everything below
        it. Each image is drawn at ``rect.topleft`` moved by its ``image_pos``.
        Drawing changes nothing, so it can run any number of times per update.

        Args:
            surface: Surface to draw on, usually the display surface. It should
                be the size the UI was created with.
        """
        for widget in self.root._iter_visible_subtree():
            surface.blit(
                widget.image,
                (
                    widget.rect.left + widget.image_pos[0],
                    widget.rect.top + widget.image_pos[1],
                ),
            )
