def _hard_break_word(font, word, max_width):
    """Split a single word into chunks if it is wider than max_width."""
    if not word:
        return [""]
    lines = []
    cur = ""
    for ch in word:
        trial = cur + ch
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines if lines else [word]


def _wrap_words_to_width(font, text, max_width):
    """Word-wrap text so each line fits within max_width pixels."""
    if max_width < 16:
        return [text] if text else [""]
    raw = (text or "").strip()
    if not raw:
        return [""]
    words = raw.split()
    lines = []
    cur = words[0]
    if font.size(cur)[0] > max_width:
        hb = _hard_break_word(font, cur, max_width)
        lines.extend(hb[:-1])
        cur = hb[-1] if hb else ""
        words = words[1:]
    else:
        words = words[1:]
    for word in words:
        trial = cur + " " + word
        if font.size(trial)[0] <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            if font.size(cur)[0] > max_width:
                hb = _hard_break_word(font, cur, max_width)
                lines.extend(hb[:-1])
                cur = hb[-1] if hb else ""
    if cur:
        lines.append(cur)
    return lines
