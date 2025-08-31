# ForgottenPythonScripts
A place to hold all my projects, scripts, and files related to my ForgottenLanguages.org journey
Here you go—drop this straight into LipsumLab/README.md.

⸻

LipsumLab

Reversible, theme-aware Lorem Ipsum for any language (plus a handful of stylish pseudo-languages).
Encode real text → themed filler that still decodes back exactly; or decode previous themed text using its mapping ID.

⸻

Why this exists
	•	Designers want nice-looking filler, but teams also want to recover what was there.
	•	Writers want theme variety (classic latin, cyberpunk, biotech, language-native vibes).
	•	Hackers want it deterministic and reversible for audits and redaction workflows.

LipsumLab maps each source word to a single theme token (length-aware), stores the mapping, and can decode later using the generated map ID.

⸻

Features
	•	Reversible themed encoding: one source token → one theme token (consistent within a mapping).
	•	Length matching with soft tolerance; graceful synthetic tokens when needed.
	•	Multiple themes:
	•	latin (built-in), and any file in lexicons/*.txt (e.g., en.txt, es.txt, cyberpunk.txt, biotech.txt, etc.)
	•	Language-aware lexicon builders:
	•	Local builder from any UTF-8 corpus (lexicon_builder.py)
	•	Wikipedia auto-fetch builder (web_corpus_builder.py)
	•	USAS bulk importer (scripts/usas_bulk_pull.py)
	•	Large inputs: streams text, supports multi-thousand character blocks.
	•	Artifacts:
	•	Encoded text saved under LanguageToIpsum/…
	•	Decoded text saved under IpsumToLanguage/…
	•	Reversible maps saved as JSON under mappings/… with a stable UUID you can keep.

⸻

Repository layout

LipsumLab/
├── li_manager.py                # Main TUI orchestrator (encode/decode, save outputs)
├── li_reversible_themed.py      # Core reversible encoder/decoder + theme mechanics
├── lexicon_builder.py           # Build a lexicon from a local corpus (TXT)
├── web_corpus_builder.py        # Build a lexicon by fetching Wikipedia text
├── scripts/
│   ├── usas_to_wordlist.py      # Convert USAS TSV → one-word-per-line
│   └── usas_bulk_pull.py        # Bulk pull & convert many languages from USAS repo
├── lexicons/                    # Theme wordlists (one word per line, UTF-8)
│   ├── latin.txt                # Built-in classic lorem (optional file; also in code)
│   ├── en.txt, es.txt, fr.txt…  # Your language and themed lexicons live here
├── mappings/                    # JSON maps from last encodes (keyed by UUID)
├── LanguageToIpsum/             # Saved themed outputs (encode direction)
└── IpsumToLanguage/             # Saved decoded outputs (decode direction)

If the folders don’t exist yet, the scripts will create them on first run.

⸻

Quick start

1) Create and activate a virtual environment (macOS/Linux)

python3 -m venv .venv
source .venv/bin/activate

2) Install optional helpers (recommended)

pip install requests jieba pythainlp

	•	requests → Wikipedia fetcher
	•	jieba → Chinese segmentation
	•	pythainlp → Thai segmentation

LipsumLab’s core encoder/decoder doesn’t require these, but the web lexicon builder benefits from them.

3) Run the manager

cd LipsumLab
python li_manager.py

You’ll see:

Choose an action:
  1) Translate ANY → LI (reversible; saves mapping)
  2) Translate LI → Original (requires mapping ID)
Enter 1 or 2:

	•	Encoding (1): Pick a source language code (e.g., en) and choose a theme (latin or a file in lexicons/ like es, cyberpunk, etc.). Paste text or provide a file path. The tool outputs:
	•	Encoded text saved in LanguageToIpsum/<Lang>To<Theme>_<timestamp>.txt
	•	Mapping JSON saved in mappings/<uuid>.json
	•	The console prints [LI-MAP-ID: <uuid>]—save it.
	•	Decoding (2): Paste the themed text and supply the map ID printed during encoding. The original text is reconstructed and saved under IpsumToLanguage/<Theme>To<Lang>_<timestamp>.txt.

⸻

Creating or importing lexicons

LipsumLab uses simple UTF-8 wordlists, one word per line, lowercase, no punctuation. File name = theme key (e.g., pt.txt, biotech.txt).

Option A — Build from a local corpus

# Example: download a public-domain English text quickly
curl -o english_corpus.txt https://www.gutenberg.org/files/1661/1661-0.txt

# Build a 500-word lexicon
python -c "from lexicon_builder import build_lexicon_file; \
           build_lexicon_file('english_corpus.txt','lexicons/en.txt')"

This builder:
	•	tokenizes to letters only,
	•	removes digits/punct,
	•	caps short tokens (≤3 chars) at ~15%,
	•	balances lengths (4–6, 7–10, 11–14),
	•	de-duplicates in approximate frequency order.

Option B — Auto-build from Wikipedia (per language)

python web_corpus_builder.py es --dest lexicons --articles 60 --min_chars 15000 --max_words 500

	•	Fetches random Spanish Wikipedia pages, extracts plaintext, builds lexicons/es.txt.

Option C — Import from UCREL Multilingual-USAS (bulk)
	1.	Clone the repo (outside your project):

cd ~/Downloads
git clone --depth 1 https://github.com/UCREL/Multilingual-USAS.git

	2.	Convert many languages in one go:

cd /path/to/LipsumLab
python scripts/usas_bulk_pull.py \
  ~/Downloads/Multilingual-USAS \
  ./lexicons \
  --langs "ar bg ca cs da et fi fil fr he hi hr hu id it ka lt lv mk ms nl no pl pt ro ru sl sq sr sv th tr uk vi zh"

The script finds each language’s single-word TSV (skips “mwe”), converts it to simple lists, and writes lexicons/<code>.txt.

License note (USAS): Most non-English semantic lexicons are CC BY-NC-SA 4.0. Preserve attribution and avoid commercial use unless the file says otherwise.

⸻

Theming choices

You can choose any file under lexicons/ as the theme key. Good defaults:
	•	latin — classic “lorem ipsum” style (built-in and/or lexicons/latin.txt)
	•	en, es, fr, … — language-native look
	•	Fun sets like cyberpunk.txt, biotech.txt, umbralisk.txt (your own curated lists)

Reversibility depends on the saved mapping, not the theme itself. You can always decode if you kept the map JSON (or its ID).

⸻

Reversibility, maps, and IDs
	•	Each encode run creates a mapping between source tokens and theme tokens.
	•	Mapping is saved as mappings/<uuid>.json and the UUID is printed as:

[LI-MAP-ID: 555eedb4-fc69-46dc-ae9c-4dc2b7190fbb]


	•	To decode, you need either the JSON file or the UUID string (the manager looks it up in mappings/).

If you lose the map, decoding cannot be guaranteed; reversible encoding is map-dependent by design.

⸻

Quality knobs (if the output “looks weird”)
	•	Use a different theme if you don’t like the vibe (latin is pretty).
	•	Strengthen the lexicon:
	•	Use richer corpora or increase --articles/--min_chars in the web builder.
	•	Filter stopwords more aggressively in lexicon_builder.py (see EN_STOP) or add a relevant stopword set for your language.
	•	Lower synthesis by widening the length window: in li_reversible_themed.py, allow ±2 length tolerance to pick real words more often and synthesize less.

⸻

Example sessions

Encode English → Latin

$ python li_manager.py
Choose an action:
  1) Translate ANY → LI (reversible; saves mapping)
  2) Translate LI → Original (requires mapping ID)
Enter 1 or 2: 1
Source language code (e.g., 'en', 'es', 'fr'): en
Use a THEME matching the language code? [y/N]: n
Choose theme key (available in ./lexicons): latin
Paste or type your text below. Finish with a single line 'END'
Since the incident with balloons flying ...
END

[LI-MAP-ID: 2f6a...]
Saved: LanguageToIpsum/EnglishToLatin_20250829_1452.txt
Saved map: mappings/2f6a....json

Decode (Latin → English)

$ python li_manager.py
Enter 1 or 2: 2
Paste themed text, then 'END' ...
[... themed text ...]
END
Enter LI-MAP-ID (UUID): 2f6a...
Saved: IpsumToLanguage/LatinToEnglish_20250829_1457.txt


⸻

API notes (developers)
	•	Core encoder/decoder functions live in li_reversible_themed.py:
	•	encode_to_theme(text, theme_words, lang='en') -> (encoded_text, mapping_dict)
	•	decode_from_theme(text, mapping_dict) -> original_text
	•	Themes are simple lists (Python list[str]). Loaders read lexicons/<key>.txt.
	•	Mapping JSON schema is straightforward: { "keyed_by": "source", "pairs": { "source_token": "theme_token", ... }, "meta": {...} }.

⸻

Performance
	•	Works linearly over tokens; practical throughput is dominated by I/O and tokenization.
	•	Large inputs (10k–100k chars) are fine. If you hit memory issues, process in chunks; the mapping remains consistent for a single run.

⸻

Troubleshooting
	•	“FileNotFoundError: corpus not found”
Use absolute paths or run from the project folder. pwd to confirm.
	•	“Strange English output (are/now/face repeated)”
Your English lexicon contains too many function words. Rebuild with stronger stopword filtering or use another theme like latin.
	•	Chinese/Thai results look unsegmented
Install jieba / pythainlp and rebuild the lexicon with web_corpus_builder.py.

⸻

Security & privacy
	•	No source text is sent anywhere unless you use the Wikipedia builder (which only pulls public text).
	•	Mappings and outputs are stored locally. Handle mappings/*.json as sensitive metadata if your source text is sensitive.

⸻

Licensing
	•	Core project code: you own your instance.
	•	Lexicons you generate from Wikipedia/Gutenberg: store word lists only (facts/words are generally non-copyrightable), but don’t redistribute large text excerpts.
	•	USAS imports: respect the CC BY-NC-SA 4.0 license where applicable; keep attribution and avoid commercial use unless licensed otherwise.

⸻

Roadmap (optional ideas)
	•	Phrase-level reversible encoding (multi-token blocks).
	•	Per-POS theming (verbs/nouns get separate lists).
	•	Noise-resilient decoding (recover with partial maps).
	•	Zip bundler for lexicon packs + manifests.

⸻

Credits
	•	Concept, direction, and orchestration by CupofJavad.
	•	Core engineering & documentation: project contributors.
	•	Data sources: Wikipedia / MediaWiki API, Project Gutenberg, UCREL Multilingual-USAS (Lancaster University).
	•	Special thanks to the open-source community for segmentation and NLP tooling.

Happy theming. Keep your maps safe, your tokens tidy, and your lorem spicy.