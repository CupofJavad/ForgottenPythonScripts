#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
li_reversible_themed.py — Reversible Themed Ipsum Encoder/Decoder

Encode: ANY language/text -> THEMED IPSUM using a chosen lexicon (Latin, Cyberpunk, etc.)
Decode: THEMED IPSUM -> ORIGINAL text (lossless) using saved mapping

Features
- Reversible mapping saved in ./mappings/<UUID>.json
- Auto-discovers lexicons from ./lexicons/*.txt or *.lex (one word per line; UTF-8)
- Unicode-friendly tokenization (works for non-Latin scripts)
- Language code picker (ISO-ish) for metadata; marks which have lexicon files
- Length-near replacements, casing preserved, punctuation/whitespace preserved
- Synthesizes extra theme-looking tokens if lexicon runs short, ensuring uniqueness
"""

import os
import re
import sys
import json
import uuid
import time
import hashlib
import random
from typing import Dict, List, Tuple

# ----------------------------
# Paths / dirs
# ----------------------------

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(APP_DIR, "mappings")
LEX_DIR = os.path.join(APP_DIR, "lexicons")
os.makedirs(MAP_DIR, exist_ok=True)

# ----------------------------
# Language names (for metadata picker)
# ----------------------------

LANG_NAMES = {
    "sq": "Shqip (Albanian)", "ar": "العربية (Arabic)", "bg": "Български (Bulgarian)",
    "ca": "Català (Catalan)", "zh": "中文简体 (Chinese, Simplified)", "hr": "Hrvatski (Croatian)",
    "cs": "Česky (Czech)", "da": "Dansk (Danish)", "nl": "Nederlands (Dutch)",
    "en": "English", "et": "Eesti (Estonian)", "fil": "Filipino", "fi": "Suomi (Finnish)",
    "fr": "Français (French)", "ka": "ქართული (Georgian)", "de": "Deutsch (German)",
    "el": "Ελληνικά (Greek)", "he": "עברית (Hebrew)", "hi": "हिन्दी (Hindi)",
    "hu": "Magyar (Hungarian)", "id": "Indonesia (Indonesian)", "it": "Italiano (Italian)",
    "lv": "Latviski (Latvian)", "lt": "Lietuviškai (Lithuanian)", "mk": "македонски (Macedonian)",
    "ms": "Melayu (Malay)", "no": "Norsk (Norwegian)", "pl": "Polski (Polish)",
    "pt": "Português (Portuguese)", "ro": "Română (Romanian)", "ru": "Русский (Russian)",
    "sr": "Српски (Serbian)", "sl": "Slovenščina (Slovenian)", "es": "Español (Spanish)",
    "sv": "Svenska (Swedish)", "th": "ไทย (Thai)", "tr": "Türkçe (Turkish)",
    "uk": "Українська (Ukrainian)", "vi": "Tiếng Việt (Vietnamese)",
}

def discover_lexicon_codes(folder: str = LEX_DIR) -> set:
    codes = set()
    if os.path.isdir(folder):
        for fname in os.listdir(folder):
            if fname.startswith("."):
                continue
            if fname.endswith(".txt") or fname.endswith(".lex"):
                code = os.path.splitext(fname)[0].lower()
                if 2 <= len(code) <= 40:
                    codes.add(code)
    return codes

# ----------------------------
# Tokenization & casing (Unicode-friendly)
# ----------------------------

# group 1 = "word" (letters only), group 2 = everything else (punct/whitespace/digits)
TOKEN_RE = re.compile(r"([^\W\d_]+|[\W\d_]+)", re.UNICODE)

def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text)

def casing_type(word: str) -> str:
    if word.isupper():
        return "upper"
    if word[:1].isupper() and word[1:].islower():
        return "title"
    if word.islower():
        return "lower"
    return "mixed"

def apply_casing(src_form: str, dest_lower: str) -> str:
    c = casing_type(src_form)
    if c == "upper":
        return dest_lower.upper()
    if c == "title":
        return dest_lower.capitalize()
    if c == "lower":
        return dest_lower
    return dest_lower

# ----------------------------
# Built-in Latin lexicon (fallback if no file provided)
# ----------------------------

BUILTIN_LATIN = [
    "lorem","ipsum","dolor","sit","amet","consectetur","adipiscing","elit","sed","do","eiusmod",
    "tempor","incididunt","ut","labore","et","dolore","magna","aliqua","enim","minim","veniam",
    "quis","nostrud","exercitation","ullamco","laboris","nisi","aliquip","ex","ea","commodo",
    "consequat","duis","aute","irure","in","reprehenderit","voluptate","velit","esse","cillum",
    "eu","fugiat","nulla","pariatur","excepteur","sint","occaecat","cupidatat","non","proident",
    "sunt","culpa","qui","officia","deserunt","mollit","anim","id","est","laborum",
    "praesent","gravida","luctus","ultricies","facilisi","taciti","sociosqu","nascetur","ridiculus","mus",
    "pharetra","vehicula","varius","dapibus","congue","porta","bibendum","hendrerit","pulvinar","placerat",
    "maximus","efficitur","dictum","finibus","sollicitudin","integer","fermentum","curabitur","phasellus","malesuada",
    "morbi","urna","nibh","ligula","sapien","commodo","ornare","vivamus","accumsan","fusce",
    "torquent","per","conubia","nostra","per","inceptos","himenaeos","class","aptent","taciti",
    "arcu","tellus","semper","fames","montes","natoque","penatibus","magnis","dis","parturient",
    "tristique","senectus","netus","etiam","rhoncus","temporibus","habitant","platea","dictumst","tempus",
    "aliquet","iaculis","suscipit","dignissim","laoreet","condimentum","auctor","scelerisque","efficiendi",
    "praesentium","voluptatum","dolorum","expedita","quibusdam","ratione","aspernatur","illum",
    "delectus","reiciendis","laudantium","aperiam","quaerat","beatae","distinctio","veritatis","numquam",
    "necessitatibus","ad","nihil","magni","omnis","ducimus","asperiores","excepturi","repellendus","temporis",
    "et","ut","at","ac","nec","non","per","cum","sub","supra","post","ante","circa","pro","quo","qua","nam","sed","aut","vel","ne",
]

PREFERRED_ENDINGS_PLURAL = ("a","ae","i","es","um","us")

# ----------------------------
# Lexicon loading & synthesis helpers
# ----------------------------

def load_lexicon_from_file(path: str) -> List[str]:
    words: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for w in line.split():
                    w = w.strip()
                    if w:
                        words.append(w)
    except Exception as e:
        print(f"[WARN] Failed to read lexicon '{path}': {e}", file=sys.stderr)
    seen = set(); out = []
    for w in words:
        lw = w.strip()
        if lw and lw not in seen:
            seen.add(lw); out.append(lw)
    return out

def discover_lexicons(folder: str = LEX_DIR) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    if os.path.isdir(folder):
        for fname in sorted(os.listdir(folder)):
            if fname.startswith("."):
                continue
            if not (fname.endswith(".txt") or fname.endswith(".lex")):
                continue
            key = os.path.splitext(fname)[0].lower()
            words = load_lexicon_from_file(os.path.join(folder, fname))
            if words:
                found[key] = words
    if "latin" not in found:
        found["latin"] = BUILTIN_LATIN[:]  # fallback built-in
    return found

def build_syllables_from_lexicon(words: List[str]) -> List[str]:
    chunks: List[str] = []
    for w in words:
        lw = w.lower()
        lw = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", lw)
        for size in (2, 3):
            for i in range(0, max(0, len(lw) - size + 1), size):
                piece = lw[i:i+size]
                if len(piece) >= 2 and piece.isalpha():
                    chunks.append(piece)
    if not chunks:
        chunks = ["lo","rem","ip","sum","ne","on","vec","tor","syn","th"]
    seen = set(); out = []
    for c in chunks:
        if c not in seen:
            seen.add(c); out.append(c)
    return out

def synthesize_from_theme(target_len: int, seed_int: int, syllables: List[str], used: set) -> str:
    rng = random.Random(seed_int)
    token = ""
    while len(token) < target_len:
        token += rng.choice(syllables)
    token = token[:target_len]
    base = token; n = 1
    while token in used:
        token = (base + rng.choice(["x","um","us","ix","on","a"]))[:max(target_len, len(base)+1)]
        n += 1
        if n > 10 and token in used:
            token = f"{base}{n}"
    return token

# ----------------------------
# Mapping persistence
# ----------------------------

def save_mapping(map_id: str, forward_map: Dict[str, str], meta: Dict) -> str:
    """
    Saves mapping to ./mappings/<id>.json
    forward_map: src_lower -> themed_lower
    meta: {created, source_lang, theme_key, theme_name}
    """
    path = os.path.join(MAP_DIR, f"{map_id}.json")
    payload = {
        "id": map_id,
        "created": meta.get("created"),
        "source_lang": meta.get("source_lang", "unknown"),
        "theme_key": meta.get("theme_key", ""),
        "theme_name": meta.get("theme_name", ""),
        "note": "forward_map is src_lower -> themed_lower; reverse is derivable.",
        "forward_map": forward_map,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path

def load_reverse_map(map_id: str) -> Tuple[Dict[str, str], Dict]:
    path = os.path.join(MAP_DIR, f"{map_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    fwd = data["forward_map"]
    rev = {v: k for k, v in fwd.items()}
    return rev, data

# ----------------------------
# Core encode/decode
# ----------------------------

def pick_theme_replacement(src_lower: str,
                           desired_len: int,
                           used: set,
                           rng: random.Random,
                           theme_words: List[str],
                           theme_syllables: List[str]) -> str:
    pluralish = src_lower.endswith("s")
    candidates = [w for w in theme_words if abs(len(w) - desired_len) <= 1 and w.lower() not in used]
    if pluralish:
        prioritized = [w for w in candidates
                       if w.lower().endswith(("a","ae","i","es","um","us"))]
        if prioritized:
            candidates = prioritized
    if candidates:
        choice = rng.choice(candidates).lower()
        used.add(choice)
        return choice
    seed_int = int(hashlib.sha256(src_lower.encode("utf-8")).hexdigest(), 16)
    synth = synthesize_from_theme(max(3, desired_len), seed_int, theme_syllables, used)
    used.add(synth)
    return synth

def encode_to_theme(text: str,
                    source_lang: str,
                    theme_key: str,
                    theme_name: str,
                    theme_words: List[str]) -> Tuple[str, str]:
    """
    Returns (output_with_header, map_id)
    """
    rng = random.Random(42)  # stable candidate order
    forward_map: Dict[str, str] = {}
    used_theme: set = set()
    theme_syllables = build_syllables_from_lexicon(theme_words)

    out: List[str] = []
    for tok in tokenize(text):
        if tok.isalpha():
            src_lower = tok.lower()
            if src_lower in forward_map:
                themed_lower = forward_map[src_lower]
            else:
                themed_lower = pick_theme_replacement(src_lower, len(tok), used_theme, rng,
                                                      theme_words, theme_syllables)
                forward_map[src_lower] = themed_lower
            out.append(apply_casing(tok, themed_lower))
        else:
            out.append(tok)

    map_id = str(uuid.uuid4())
    meta = {
        "created": int(time.time()),
        "source_lang": source_lang,
        "theme_key": theme_key,
        "theme_name": theme_name,
    }
    save_mapping(map_id, forward_map, meta)

    header = f"[LI-MAP-ID: {map_id}] [THEME: {theme_key}] [LANG: {source_lang}]\n"
    return header + "".join(out), map_id

HEADER_RE = re.compile(r"\[LI-MAP-ID:\s*([0-9a-fA-F-]{36})\]")

def extract_map_id(text: str) -> Tuple[str, str]:
    m = HEADER_RE.search(text)
    if not m:
        return text, ""
    map_id = m.group(1)
    new_text = text.replace(m.group(0), "").lstrip("\n")
    return new_text, map_id

def decode_to_original(text: str, map_id: str) -> str:
    rev_map, _meta = load_reverse_map(map_id)
    out: List[str] = []
    for tok in tokenize(text):
        if tok.isalpha():
            themed_lower = tok.lower()
            if themed_lower in rev_map:
                src_lower = rev_map[themed_lower]
                out.append(apply_casing(tok, src_lower))
            else:
                out.append(tok)
        else:
            out.append(tok)
    return "".join(out)

# ----------------------------
# Minimal CLI (optional)
# ----------------------------

def _read_multiline() -> str:
    print("\nPaste or type your text below.")
    print("When finished, type a single line with: END")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def _menu() -> str:
    print("\nChoose an action:")
    print("  1) Encode ANY → THEME (reversible)")
    print("  2) Decode THEME → ORIGINAL (requires mapping ID)")
    return input("Enter 1 or 2: ").strip()

def main():
    from datetime import datetime
    choice = _menu()
    lexicons = discover_lexicons(LEX_DIR)

    if choice == "1":
        # pick language (metadata only)
        codes = sorted(LANG_NAMES.keys())
        print("\nLanguages:")
        print("  " + " ".join(codes))
        source_lang = input("Source language code (or blank): ").strip().lower() or "unknown"

        # pick theme
        keys = sorted(lexicons.keys())
        for i, k in enumerate(keys, 1):
            print(f"  {i}) {k} ({len(lexicons[k])} words)")
        idx = int(input("Pick theme number: ").strip() or "1")
        idx = max(1, min(idx, len(keys)))
        theme_key = keys[idx-1]
        theme_name = theme_key.title() + " Ipsum"

        text = _read_multiline().strip()
        if not text:
            print("No input text.", file=sys.stderr); sys.exit(1)
        out, map_id = encode_to_theme(text, source_lang, theme_key, theme_name, lexicons[theme_key])
        print("\n===== OUTPUT START =====\n")
        print(out)
        print("\n===== OUTPUT END =====\n")
        print(f"Saved mapping: {os.path.join(MAP_DIR, map_id + '.json')}")

    elif choice == "2":
        themed = _read_multiline().strip()
        themed_wo, mid = extract_map_id(themed)
        if not mid:
            mid = input("Enter mapping UUID: ").strip()
        if not mid:
            print("No mapping id.", file=sys.stderr); sys.exit(1)
        restored = decode_to_original(themed_wo, mid)
        print("\n===== OUTPUT START =====\n")
        print(restored)
        print("\n===== OUTPUT END =====\n")
    else:
        print("Invalid choice.", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()