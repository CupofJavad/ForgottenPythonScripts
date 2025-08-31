#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lexicon_builder.py — Build a themed lexicon from any UTF-8 corpus text.

Exports:
- build_lexicon(corpus_text: str, min_len=3, max_len=14, max_words=500) -> list[str]
- build_lexicon_file(src_path: str, dest_path: str, **kwargs) -> str

Strategy:
- Lowercase and split on non-letter (Unicode-aware)
- Frequency-sort and keep unique words respecting length bounds
- Write one word per line (UTF-8)
- Returns a balanced 200–500+ words list (configurable)
"""

import re
from collections import Counter
from typing import List

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# add near top
EN_STOP = {
    "the","be","to","of","and","a","in","that","have","i","it","for","not","on","with","he","as","you","do","at",
    "this","but","his","by","from","they","we","say","her","she","or","an","will","my","one","all","would","there",
    "their","what","so","up","out","if","about","who","get","which","go","me","when","make","can","like","time",
    "no","just","him","know","take","people","into","year","your","good","some","could","them","see","other","than",
    "then","now","look","only","come","its","over","think","also","back","after","use","two","how","our","work",
    "first","well","way","even","new","want","because","any","these","give","day","most","us","are","is","am","was",
    "were","been","being","had","has","have","did","does","doing","shall","should","might","must","may"
}

def build_lexicon(corpus_text: str,
                  min_len: int = 3,
                  max_len: int = 14,
                  max_words: int = 500) -> List[str]:
    txt = corpus_text.lower()
    tokens = WORD_RE.findall(txt)

    # strip obvious numerics and possessives like "holmes's"
    tokens = [re.sub(r"^'+|'+$", "", t) for t in tokens]
    tokens = [t for t in tokens if not t.isdigit()]

    freq = Counter(tokens)

    # initial candidate list by freq, length, and stopword filter
    cand = [w for w,_ in freq.most_common()
            if min_len <= len(w) <= max_len and w not in EN_STOP]

    # enforce length balance: cap very short words
    short_cap = int(max_words * 0.15)  # ≤3 chars cap ~15%
    out, seen = [], set()
    short_count = 0

    def push(w):
        nonlocal short_count
        if w in seen: return False
        if len(w) <= 3 and short_count >= short_cap: return False
        seen.add(w)
        out.append(w)
        if len(w) <= 3: short_count += 1
        return True

    for w in cand:
        if len(out) >= max_words: break
        push(w)

    # if still too few, relax a bit on stopwords (but keep short cap)
    if len(out) < max_words:
        for w,_ in freq.most_common():
            if min_len <= len(w) <= max_len and w not in seen:
                push(w)
            if len(out) >= max_words: break

    return out

def build_lexicon(corpus_text: str,
                  min_len: int = 3,
                  max_len: int = 14,
                  max_words: int = 500) -> List[str]:
    txt = corpus_text.lower()
    tokens = WORD_RE.findall(txt)
    # frequency, then prune by length
    freq = Counter(tokens)
    words = [w for w, _ in freq.most_common() if min_len <= len(w) <= max_len]
    # unique while preserving rank order
    out = []
    seen = set()
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= max_words:
            break
    # ensure length variety: if too few short/long words, we relax a bit
    if len(out) < 150 and max_len < 20:
        # widen length to pull more candidates
        more = [w for w, _ in freq.most_common() if 2 <= len(w) <= 20 and w not in seen]
        for w in more:
            seen.add(w); out.append(w)
            if len(out) >= max_words:
                break
    return out

def build_lexicon_file(src_path: str,
                       dest_path: str,
                       min_len: int = 3,
                       max_len: int = 14,
                       max_words: int = 500) -> str:
    with open(src_path, "r", encoding="utf-8") as f:
        corpus = f.read()
    words = build_lexicon(corpus, min_len=min_len, max_len=max_len, max_words=max_words)
    with open(dest_path, "w", encoding="utf-8") as f:
        for w in words:
            f.write(w + "\n")
    return dest_path