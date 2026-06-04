"""Shared header rendering for editor screens."""



def draw_header(session, title, hint, w):
    surf = session.font_title.render(title, True, session.title)
    session.screen.blit(surf, ((w - surf.get_width()) // 2, 24))
    hint_s = session.font_hint.render(hint, True, session.title)
    session.screen.blit(hint_s, ((w - hint_s.get_width()) // 2, 24 + surf.get_height() + 8))
