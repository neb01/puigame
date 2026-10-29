"""UI, the object a game uses to create and run a set of widgets.

A UI holds a UIRoot, the top of its widget tree, which holds the theme. It lays
out the tree, passes input to it, and draws it, each widget above its parent. A
top-level widget is created with ``ui.root`` as its parent, and
``handle_event()``, ``update()``, and ``draw()`` run the UI each frame. A screen
that shows several UIs at once, such as a pause menu over a HUD, uses a separate
UI for each, with the game deciding their order.
"""

import pygame as pg
from pygame.typing import Point

from puigame._styling.theme import DEFAULT_THEME, Theme
from puigame.core.ui_manager import UIManager
from puigame.core.ui_root import UIRoot

# one frame at 60 fps, for games that update once per fixed-rate frame
DEFAULT_DT = 1 / 60


class UI:
    """A widget tree, with its layout and drawing, run by the game each frame.

    The UI lays out and draws on a surface of the ``size`` given on creation,
    and its rects are in that surface's pixels. Each frame, the game passes
    each event to ``handle_event()``, then calls ``update()``, then ``draw()``.
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
        self._manager = UIManager(root=self.root)

    @property
    def root(self) -> UIRoot:
        """The widget at the top of the UI's tree, the parent of top-level widgets.

        Set on creation and never changed, so it is read-only.
        """
        return self._root

    def handle_event(self, event: pg.Event) -> bool:
        """Handle one pygame event and report whether the UI consumed it.

        Pass every event, not only mouse events, before ``update()`` each
        frame. The UI ignores events it has no use for, but needs window events
        such as ``WINDOWLEAVE`` and ``WINDOWFOCUSLOST`` to keep the highlight
        and presses right. It never polls pygame itself, so it sees only the
        events it is given. Event positions must be in the coordinates of the
        UI's draw surface.

        A mouse button down over a widget that consumes clicks is consumed, and
        so is its matching up, wherever it lands, so a click on a panel never
        reaches the game. A drag that starts outside the UI still reaches the
        game when it is released over a widget. Mouse motion, wheel, and window
        events are never consumed.

        Args:
            event: The event to handle.

        Returns:
            ``True`` if the UI consumed the event, so the game should not handle
            it, otherwise ``False``.
        """
        return self._manager.handle_event(event)

    def update(self, dt: float = DEFAULT_DT) -> None:
        """Lay out the widgets and refresh their images for this frame.

        Call once per frame, after handling events and before ``draw()``.
        Changes made to widgets since the last update, such as a new offset or
        flag, take effect here: the layout pass places every widget against its
        parent, the highlight moves to the widget under the cursor, then each
        widget shows its image for its current state.

        Args:
            dt: Time since the last frame, in seconds. Defaults to
                ``DEFAULT_DT``, one frame at 60 fps. Games running at another
                or a variable frame rate pass the real elapsed time, for
                example ``clock.tick(fps) / 1000``.
        """
        self.root._place_tree()
        self._manager._update_highlight()
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
