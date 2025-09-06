# ForgottenPythonScripts

A research playground to test the hypothesis that some of the “gibberish” on Forgotten Languages is not a natural language at all, but reversible Lorem-Ipsum–style encodings created with a secret mapping + lexicon.  

Site reference: https://forgottenlanguages-full.forgottenlanguages.org/

This repo hosts two main workstreams:  
1. `LipsumLap/` — a reversible Lorem-Ipsum encoder/decoder pipeline for generating theme-aware filler and testing decryption strategies.  
2. `WebScraping/` — utilities to crawl/clean content (including FL pages) into structured text corpora you can analyze.  

There’s also `FL Text Cleaned Up/` for language-targeted extraction from scraped dumps to isolate English or specific non-English snippets for study.

Credit: Concept, direction, and orchestration by CupofJavad.  
Engineering & documentation support by collaborators and the open-source community.  

---

## Background & Hypothesis

The Forgotten Languages archive contains posts ranging from readable English to baffling strings that sound language-like but remain undeciphered. The working theory here:  

The “FL language” could be deterministic Lorem-Ipsum encoding using:  
- a lexicon (wordlist) to shape the look/feel of the text, and  
- a mapping from original tokens → themed tokens, reversible with the correct map.  

If that’s true, then building a high-fidelity LI encoder/decoder and comparing many encodes against FL “gibberish” should reveal recurring mapping motifs and lexicon fingerprints.  

This repo provides the tooling to recreate such encodings, scrape candidate data, clean it, and compare.  

---

## Repository Layout

```text
ForgottenPythonScripts/
├── LipsumLap/                  # Reversible Lorem Ipsum engine + lexicon tooling
│   ├── li_manager.py           # TUI: encode/decode; saves outputs + mapping UUID
│   ├── li_reversible_themed.py # Core encoder/decoder (length-aware, reversible)
│   ├── lexicon_builder.py      # Build wordlists from local corpora (UTF-8 .txt)
│   ├── web_corpus_builder.py   # Build wordlists by sampling Wikipedia text
│   └── scripts/
│       ├── usas_to_wordlist.py # Convert USAS TSV → one-word-per-line lists
│       └── usas_bulk_pull.py   # Bulk import/convert many languages from USAS
├── lexicons/                   # Drop .txt wordlists here (one token/line)
├── mappings/                   # JSON maps (per-encode) keyed by UUID
├── LanguageToIpsum/            # Encoded outputs (source→theme)
├── IpsumToLanguage/            # Decoded outputs (theme→source via map)
├── WebScraping/
│   ├── web_scraper_cleaned.py  # Crawl a domain/URL; save each page as text file
│   └── combine_texts.py        # Merge per-page files into one or few corpora
├── FL Text Cleaned Up/
│   └── extractor.py            # Language-targeted extraction from mixed FL dumps
└── samples/                    # Example input/output corpora (optional)
```

> Note: earlier notes used “LipsumLab”; the current working directory name is **LipsumLap**.

---

## Quick Setup

```bash
# From repo root
python3 -m venv .venv
source .venv/bin/activate

# Core helpers (recommended)
pip install requests jieba pythainlp beautifulsoup4 lxml tldextract

# If you plan to import USAS lexicons:
# (You clone the repo separately; see instructions below in the LipsumLap section)
```

---

## 1) LipsumLap — Reversible Lorem-Ipsum Engine

### Purpose
- Generate themed, reversible encodings of arbitrary text.  
- Save the mapping (token↔token) to decode later.  
- Build or import lexicons for many languages/themes (Latin, English, Spanish, etc.).  
- Compare LI outputs to FL samples to hunt for lexical + mapping fingerprints.  

### How it works (high level)
- Tokenize the source text → map each unique token to a single theme token of similar length.  
- If a close-length token isn’t available, synthesize a plausible theme-like token.  
- Save `{source_token: theme_token}` in `mappings/<UUID>.json`.  
- Decoding uses that exact map to invert the process.  

### Run the manager (TUI)

```bash
cd LipsumLap
python li_manager.py
```

You’ll see:

```text
Choose an action:
  1) Translate ANY → LI (reversible; saves mapping)
  2) Translate LI → Original (requires mapping ID)
Enter 1 or 2:
```

- **Option 1 (encode):** choose a source language code (e.g., `en`) and a theme key (`latin` or any file in `lexicons/`). Paste text or provide a file path.  
  - Output saved in `LanguageToIpsum/<Lang>To<Theme>_<timestamp>.txt`  
  - Map saved as `mappings/<UUID>.json` and printed as `[LI-MAP-ID: <UUID>]`.  
- **Option 2 (decode):** paste themed text and provide the LI-MAP-ID.  
  - Output saved in `IpsumToLanguage/<Theme>To<Lang>_<timestamp>.txt`  

### Add lexicons (3 ways)

**A) Build from local corpus**

```bash
# Example: download Sherlock Holmes (public domain)
curl -o english_corpus.txt https://www.gutenberg.org/files/1661/1661-0.txt

# Build ~500 words with balanced lengths + limited short tokens
python -c "from lexicon_builder import build_lexicon_file; \
           build_lexicon_file('english_corpus.txt','lexicons/en.txt')"
```

**B) Auto-build from Wikipedia**

```bash
python web_corpus_builder.py es --dest lexicons --articles 60 --min_chars 15000 --max_words 500
```

**C) Import from UCREL Multilingual-USAS (bulk)**

```bash
# One-time clone outside your project
cd ~/Downloads
git clone --depth 1 https://github.com/UCREL/Multilingual-USAS.git

# Convert many languages into simple wordlists:
cd /path/to/ForgottenPythonScripts/LipsumLap
python scripts/usas_bulk_pull.py \
  ~/Downloads/Multilingual-USAS \
  ./lexicons \
  --langs "ar bg ca cs da et fi fil fr he hi hr hu id it ka lt lv mk ms nl no pl pt ro ru sl sq sr sv th tr uk vi zh"
```

License note (USAS): many non-English lexicons are CC BY-NC-SA 4.0 — keep attribution and avoid commercial use unless explicitly permitted.  

---

## 2) WebScraping — Crawl & Collect Page Text

### Purpose
Acquire raw page text from target domains (e.g., FL) so you can build corpora for language-targeted extraction and LI comparison.  

### How to use

**Single run**

```bash
cd WebScraping
python web_scraper_cleaned.py \
  --start-url "https://forgottenlanguages-full.forgottenlanguages.org/" \
  --out-dir "./out/fl_pages" \
  --max-pages 1000 \
  --same-domain true \
  --delay 0.6
```

What it does:
- Walks links on the same domain (configurable), politely throttled (`--delay`).  
- Extracts main text content from each page (strips HTML/JS/CSS).  
- Saves one `.txt` per page into `out/fl_pages/`.  

**Combine many page files into a corpus**

```bash
python combine_texts.py \
  --in-dir "./out/fl_pages" \
  --out "./out/fl_corpus.txt"
```

---

## 3) FL Text Cleaned Up — Targeted Extraction

### Purpose
FL posts often mix languages (English + non-English). This folder holds language-targeted extraction to isolate one language at a time.  

**Example: extract English-readable segments**

```bash
cd "FL Text Cleaned Up"
python extractor.py \
  --in "../WebScraping/out/fl_corpus.txt" \
  --lang "en" \
  --out "./en_clean.txt"
```

**Tweak for other languages**

```bash
python extractor.py --in "../WebScraping/out/fl_corpus.txt" --lang "es" --out "./es_clean.txt"
python extractor.py --in "../WebScraping/out/fl_corpus.txt" --lang "ru" --out "./ru_clean.txt"
python extractor.py --in "../WebScraping/out/fl_corpus.txt" --lang "zh" --out "./zh_clean.txt"
```

---

## End-to-End Workflow (Suggested)

1. Get Data — run `web_scraper_cleaned.py` on FL (respect robots/TOS).  
2. Organize Data — `combine_texts.py` → consolidated corpora.  
3. Understand Data — skim, spot-check language mixes; produce `en_clean.txt`, etc.  
4. Reproduce Encoding — use LipsumLap to encode comparable samples.  
5. Compare Encodes — analyze n-grams, token-length distributions, duplication patterns vs FL samples.  
6. Determine Common Mapping & Lexicon Data — mine for mapping fingerprints.  
7. Decode Site Contents — attempt inversion with candidate lexicons.  
8. Understand Results — interpret decoded content; iterate.  

---

## Current Status (as of this commit)

- ✅ Built a reversible LI engine (LipsumLap).  
- ✅ Built scrapers and cleaners.  
- ✅ Implemented multi-language lexicon pipelines.  
- 🔎 Actively working on Step 6: mining mapping & lexicon signals.  

---

## Remaining Objectives & Next Steps

- Mapping fingerprint miner  
- Lexicon matching heuristics  
- Decode attempts at scale  
- Tooling upgrades (CLI manifest, POS-aware theming, synthesis improvements)  

---

## Notes on Legality & Ethics

- Scraping: honor robots.txt and TOS.  
- Licensing: USAS lexicons are CC BY-NC-SA 4.0.  
- Corpora: only store unique wordlists or fair-use snippets.  

---

## Credits

- Concept & direction: CupofJavad  
- Core engineering & documentation: project contributors and community packages  
- Data sources: Forgotten Languages, Wikipedia, Project Gutenberg, UCREL Multilingual-USAS  

---

*Aim steady, map carefully, and may your lorem return home with its secrets intact.*
