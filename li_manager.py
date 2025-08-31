#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
li_manager.py — Project orchestrator

Responsibilities
- Prompt user for direction (Language→Ipsum or Ipsum→Language)
- For Language→Ipsum:
    * Prompt for source language code (for metadata)
    * Prompt for THEME (lexicon key). If lexicon missing and user wants a language-matched theme
      (e.g., 'nl'), offer to build it using lexicon_builder.py from a user-provided corpus path.
    * Run reversible encode via li_reversible_themed.encode_to_theme
    * Save output to ./LanguageToIpsum/<LangName>To<ThemeName>_MMDDYY_HHMM.txt
- For Ipsum→Language:
    * Accept pasted themed text (or file path)
    * Extract or prompt for mapping UUID
    * Decode via li_reversible_themed.decode_to_original
    * Save output to ./IpsumToLanguage/<ThemeName>To<LangName>_MMDDYY_HHMM.txt
- Create all needed directories.

Only standard library.
"""

import os
import sys
from datetime import datetime
from typing import Tuple

# Import core module
import li_reversible_themed as core
from lexicon_builder import build_lexicon_file  # builder: path -> lexicon words -> saved file

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_LANG_TO_IPSUM = os.path.join(APP_DIR, "LanguageToIpsum")
OUT_IPSUM_TO_LANG = os.path.join(APP_DIR, "IpsumToLanguage")
os.makedirs(OUT_LANG_TO_IPSUM, exist_ok=True)
os.makedirs(OUT_IPSUM_TO_LANG, exist_ok=True)
os.makedirs(core.LEX_DIR, exist_ok=True)
os.makedirs(core.MAP_DIR, exist_ok=True)

# ---------- small helpers ----------

def timestamp() -> str:
    # MMDDYY_HHMM (local time)
    return datetime.now().strftime("%m%d%y_%H%M")

def sanitize_label(s: str) -> str:
    # for filenames: strip spaces and non-filename-friendly chars
    keep = []
    for ch in s:
        keep.append(ch if ch.isalnum() else "")
    out = "".join(keep)
    return out if out else "Text"

def read_multiline() -> str:
    print("\nPaste or type your text below.\nWhen finished, type a single line with: END")
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

def read_input_text() -> str:
    print("\nInput source:")
    print("  1) Paste text interactively")
    print("  2) Read from a UTF-8 file path")
    choice = input("Choose 1 or 2 (default=1): ").strip() or "1"
    if choice == "2":
        p = input("Enter path to .txt file: ").strip()
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return read_multiline()

def save_text(dirpath: str, basename: str, content: str) -> str:
    os.makedirs(dirpath, exist_ok=True)
    path = os.path.join(dirpath, basename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

# ---------- UI flows ----------

def pick_language_code() -> str:
    codes = sorted(core.LANG_NAMES.keys())
    lex_codes = core.discover_lexicon_codes(core.LEX_DIR)
    print("\nAvailable language codes (metadata):")
    line = []
    for code in codes:
        mark = "✓" if code in lex_codes else " "
        line.append(f"{code}({mark})")
        if len(line) == 10:
            print("  " + "  ".join(line)); line = []
    if line: print("  " + "  ".join(line))
    print("Legend: ✓ = you have a lexicon file matching that code in ./lexicons (optional).")
    lang = input("Source language code (or Enter to skip): ").strip().lower() or "unknown"
    if lang not in core.LANG_NAMES and lang != "unknown":
        print(f"Note: '{lang}' isn’t in the predefined list; proceeding.")
    return lang

def ensure_language_lexicon(lang_code: str) -> Tuple[str, list]:
    """
    If you want to use a THEME that equals your language code (e.g., 'nl'), ensure the lexicon exists.
    If missing, offer to build from a user-provided corpus .txt via lexicon_builder.
    Returns (theme_key, words)
    """
    lexicons = core.discover_lexicons(core.LEX_DIR)
    if lang_code in lexicons:
        return lang_code, lexicons[lang_code]

    print(f"\nNo lexicon found for '{lang_code}'.")
    choice = input("Build one now from a UTF-8 corpus file? [y/N]: ").strip().lower()
    if choice == "y":
        src = input("Path to corpus .txt (UTF-8): ").strip()
        # build and save to ./lexicons/<lang_code>.txt
        saved_path = build_lexicon_file(src, os.path.join(core.LEX_DIR, f"{lang_code}.txt"))
        print(f"Built and saved lexicon: {saved_path}")
        lexicons = core.discover_lexicons(core.LEX_DIR)  # reload
        if lang_code in lexicons:
            return lang_code, lexicons[lang_code]
        else:
            print("Lexicon still not found after build; falling back to 'latin'.")
    return "latin", core.discover_lexicons(core.LEX_DIR)["latin"]

def pick_theme() -> Tuple[str, str, list]:
    lexicons = core.discover_lexicons(core.LEX_DIR)
    keys = sorted(lexicons.keys())
    print("\nAvailable THEMES (from ./lexicons):")
    for i, k in enumerate(keys, 1):
        sample = ", ".join(lexicons[k][:3]) + ("..." if len(lexicons[k]) > 3 else "")
        print(f"  {i}) {k}  ({len(lexicons[k])} words)  e.g., {sample}")
    raw = input("Pick a theme number (default=1), or press Enter for '1': ").strip()
    idx = int(raw) if raw.isdigit() else 1
    idx = max(1, min(idx, len(keys)))
    key = keys[idx-1]
    name = "Lipsum" if key == "latin" else key.title()
    return key, name, lexicons[key]

def encode_flow():
    # Language metadata + theme selection strategy
    lang = pick_language_code()
    use_lang_theme = input("Use a THEME matching the language code? [y/N]: ").strip().lower() == "y"

    if use_lang_theme and lang != "unknown":
        theme_key, theme_words = ensure_language_lexicon(lang)
        theme_name = "Lipsum" if theme_key == "latin" else theme_key.title()
    else:
        theme_key, theme_name, theme_words = pick_theme()

    text = read_input_text().strip()
    if not text:
        print("No input text. Exiting."); sys.exit(1)

    out, map_id = core.encode_to_theme(text, lang, theme_key, theme_name, theme_words)
    print("\n===== OUTPUT START =====\n")
    print(out)
    print("\n===== OUTPUT END =====\n")
    print(f"Saved mapping: {os.path.join(core.MAP_DIR, map_id + '.json')}")
    print("Keep the header with [LI-MAP-ID: ...] so you can decode later.")

    # Save themed output
    lang_label = "Unknown" if lang == "unknown" else core.LANG_NAMES.get(lang, lang).split(" ")[0]
    # normalize labels for filename
    left = sanitize_label(lang_label)
    right = "Lipsum" if theme_key == "latin" else sanitize_label(theme_name)
    fname = f"{left}To{right}_{timestamp()}.txt"
    path = save_text(OUT_LANG_TO_IPSUM, fname, out)
    print(f"Saved themed output to: {path}")

def decode_flow():
    print("\nDecoding THEMED IPSUM back to original.")
    themed = read_input_text().strip()
    if not themed:
        print("No input text. Exiting."); sys.exit(1)

    themed_wo, embedded_id = core.extract_map_id(themed)
    map_id = embedded_id or input("Enter mapping UUID: ").strip()
    if not map_id:
        print("No mapping id. Exiting."); sys.exit(1)

    # We peek metadata for nicer filename labels
    try:
        _, meta = core.load_reverse_map(map_id)
        theme_key = meta.get("theme_key", "")
        theme_name = meta.get("theme_name", "Lipsum")
        lang_code = meta.get("source_lang", "unknown")
        lang_label = "Unknown" if lang_code == "unknown" else core.LANG_NAMES.get(lang_code, lang_code).split(" ")[0]
    except FileNotFoundError:
        print("Mapping file not found. Exiting."); sys.exit(1)

    restored = core.decode_to_original(themed_wo, map_id)
    print("\n===== OUTPUT START =====\n")
    print(restored)
    print("\n===== OUTPUT END =====\n")

    left = "Lipsum" if theme_key == "latin" else sanitize_label(theme_name)
    right = "Unknown" if lang_label == "" else sanitize_label(lang_label)
    fname = f"{left}To{right}_{timestamp()}.txt"
    path = save_text(OUT_IPSUM_TO_LANG, fname, restored)
    print(f"Saved decoded output to: {path}")

def menu() -> str:
    print("\nChoose an action:")
    print("  1) Language → Themed Ipsum (reversible; saves mapping & output)")
    print("  2) Themed Ipsum → Original (uses mapping; saves output)")
    return input("Enter 1 or 2: ").strip()

def main():
    choice = menu()
    if choice == "1":
        encode_flow()
    elif choice == "2":
        decode_flow()
    else:
        print("Invalid choice. Exiting."); sys.exit(1)

if __name__ == "__main__":
    main()