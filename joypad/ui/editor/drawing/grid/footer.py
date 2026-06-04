"""Editor footer hint bar."""


def draw_editor_footer(session, w, y):
    hints = [
        ("A", "Select / +", (107, 191, 89)),
        ("X", "Clear / −", (191, 176, 77)),
        ("B", "Back", (191, 77, 77)),
    ]
    x = w // 2 - 180
    for key, action, col in hints:
        ks = session.font_hint.render(key, True, col)
        session.screen.blit(ks, (x, y + 8))
        x += ks.get_width() + 4
        act = session.font_hint.render(action, True, session.title)
        session.screen.blit(act, (x, y + 8))
        x += act.get_width() + 24
