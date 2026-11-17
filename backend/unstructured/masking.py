"""Shared PII masking helper for B/C/D (PDPA, trap T-A19). C may move it into its guardrail module.

Team decision (John, 16 Nov): A's records are UNMASKED; B/C/D mask before the AI model or a customer sees
anything. A only uses mask_text() to COUNT personal data (emails.pii_detected), never to change records.

Rules are applied in order; earlier rules win (an 8-digit phone is masked before the 6-digit postal rule runs).
Order numbers (5 digits) and driver codes (DRV000) are deliberately left visible.

mask_text() does NOT detect personal names or street names. privacy_guard() below does (PR #13 review P1): it is
the full guard, and it must run on any text that leaves the machine (embedding endpoint, chat model).
"""
from __future__ import annotations

import re
from typing import Dict, List, Pattern, Tuple

MASK_RULES: List[Tuple[str, "re.Pattern[str]", str]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    ("nric", re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.I), "[NRIC]"),
    # Singapore numbers: 8 digits starting 3/6/8/9, optional +65 and one space/dash in the middle.
    ("phone", re.compile(r"(?<![\w$])(?:\+65[\s-]?)?[3689]\d{3}[\s-]?\d{4}(?!\d)"), "[PHONE]"),
    ("unit", re.compile(r"#\s?\d{1,3}-\d{1,5}[A-Z]?\b"), "[UNIT]"),
    ("postal", re.compile(r"(?<![\w$])(?:S(?:ingapore)?\s?)?\d{6}(?!\d)"), "[POSTAL]"),
    ("block", re.compile(r"\b(?:blk|block)\s*\d{1,4}[A-Z]?\b", re.I), "blk [BLOCK]"),
]


def _apply(rules: List[Tuple[str, Pattern[str], str]], text: str, counts: Dict[str, int]) -> str:
    for name, pattern, replacement in rules:
        text, n = pattern.subn(replacement, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text


def mask_text(text: str) -> Tuple[str, Dict[str, int]]:
    """Return (masked_text, counts per rule). Counts only include rules that matched."""
    counts: Dict[str, int] = {}
    return _apply(MASK_RULES, text, counts), counts


# ---- Full privacy guard: mask_text + street addresses + personal names ----------------------------------------------
# Rule-based and best-effort. It catches: names after a title (Mr/Mdm/Dr ...), Malay/Indian patronymics (bin, binte,
# s/o, d/o), names after a cue ("my name is", "Regards,", "Dear", "Customer:"), common Singapore given names and
# surnames in either order ("Jane Tan", "Tan Mei Ling", "Priya Sharma"), and street names ("123 Orchard Road",
# "Tampines St 11", "Ang Mo Kio Central", "Jalan Bukit Merah"). It can MISS an uncommon name with no title or cue
# (e.g. a lone foreign first name), so the default embedder stays local (nothing leaves the machine).
# Complaint wording, order numbers, driver codes, dates and amounts are left alone so retrieval still works.

_NW = r"[A-Z][a-z]+(?:['’][A-Z]?[a-z]+)?(?:-[A-Z]?[a-z]+)?"  # one Title-case name word: Tan, D'Cruz, Mary-Ann
_INITIAL = r"[A-Z](?![\w'’])"                                    # a trailing initial: "Ryan D"

# Title-case words that start sentences or greetings but are not names (case-insensitive).
_NOT_NAME = ("the|a|an|i|we|you|he|she|it|they|this|that|these|those|my|your|our|his|her|their|its|team|sir|madam|all|"
             "everyone|merlion|express|customer|customers|service|services|support|cs|again|very|so|not|still|here|"
             "there|please|order|orders|parcel|parcels|delivery|driver|sorry|regards|thanks|thank|hope|good|morning|"
             "afternoon|evening|kind|best|warm|yours|re|fw|fwd|subject|to|from|cc|on|in|at|of|for|and|or|but|if|when|"
             "why|how|what|who|is|was|are|were|be|been|no|yes|ok|okay|hi|hello|dear|hey|mr|mrs|ms|mdm|dr")
_NOT_NAME_LA = rf"(?!(?i:{_NOT_NAME})\b)"

# Words that may precede a street suffix but are not part of a street name (case-insensitive).
_NOT_STREET = ("the|a|an|my|your|our|his|her|their|its|this|that|these|those|at|on|in|to|of|from|for|near|via|by|and|"
               "or|but|is|was|are|were|be|been|along|down|up|across|over|off|main|same|wrong|right|other|next|another|"
               "any|no|not|which|what|private|public|side|busy|old|new|whole|entire|every|each|one|two|three|first|"
               "second|third|last|nearest")
_STREET_WORD_ANY = rf"(?!(?i:{_NOT_STREET})\b)[A-Za-z][A-Za-z'’-]*"
_STREET_WORD_TITLE = rf"(?!(?i:{_NOT_STREET})\b)[A-Z][a-z'’-]+"

_GIVEN = (  # common given names in Singapore; English words that are also names (May, Will, Grace ...) left out
    "Aaron|Adam|Adrian|Agnes|Ahmad|Aisyah|Alan|Alex|Alexander|Alice|Alicia|Alvin|Amanda|Amir|Aminah|Amy|Anand|Andrew|"
    "Andy|Angela|Angeline|Anita|Anitha|Ann|Anna|Anne|Anthony|Arjun|Arun|Ashley|Audrey|Azman|Benjamin|Benny|Bernard|"
    "Bryan|Calvin|Candice|Carol|Catherine|Charles|Charlene|Cheryl|Christina|Christine|Christopher|Cindy|Clara|Clarence|"
    "Daniel|Darren|Daryl|David|Deepa|Dennis|Derek|Desmond|Divya|Dominic|Edmund|Edwin|Elaine|Eleanor|Elizabeth|Emily|"
    "Eric|Esther|Eugene|Evelyn|Farah|Faridah|Farhan|Felicia|Fiona|Gabriel|Ganesh|Gary|Geraldine|Germaine|Gerald|"
    "Gordon|Hafiz|Hakim|Hannah|Haziq|Helen|Henry|Hidayah|Ian|Irene|Irfan|Isaac|Ivan|Jacqueline|Jamie|Jane|Janet|"
    "Janice|Jason|Jasmine|Jeffrey|Jennifer|Jeremy|Jerome|Jessica|Joanne|Joel|John|Jonathan|Joseph|Joshua|Joyce|Julia|"
    "Julian|Justin|Kamala|Karen|Kavitha|Kelvin|Kenneth|Kevin|Khairul|Lakshmi|Lawrence|Leonard|Linda|Lucas|Lydia|"
    "Mandy|Marcus|Maria|Mary|Matthew|Meena|Melissa|Melvin|Michael|Michelle|Mohamed|Mohammad|Mohammed|Mohd|Muhammad|"
    "Muhd|Nabil|Nadia|Nadiah|Natalie|Nathan|Nicholas|Nicole|Noor|Nur|Nurul|Patrick|Paul|Peter|Pamela|Prakash|"
    "Priscilla|Priya|Rachel|Rajesh|Ramesh|Ravi|Raymond|Rebecca|Richard|Rizwan|Ronald|Ryan|Samantha|Samuel|Sanjay|"
    "Sarah|Selvam|Serene|Sharifah|Sharon|Shirley|Siti|Sophia|Stephanie|Stephen|Steven|Sunita|Suresh|Susan|Syafiq|"
    "Syed|Terence|Teresa|Thomas|Timothy|Tiffany|Valerie|Vanessa|Victor|Vijay|Vikram|Vincent|Vivian|Wendy|William|"
    "Winston|Xavier|Yvonne|Zainal|Zulkifli")
_SURNAME = (  # Chinese surnames as romanised in Singapore; English look-alikes (See, Song, Law, Sum) left out
    "Ang|Au|Aw|Boey|Bong|Chai|Chan|Chang|Chee|Chen|Cheng|Cheong|Cheung|Chew|Chia|Chiam|Chiang|Chin|Ching|Chiu|Choi|"
    "Chong|Choo|Chow|Chu|Chua|Chuah|Chung|Fong|Foo|Gan|Goh|Gwee|Heng|Ho|Hoo|Huang|Hui|Kang|Khoo|Koh|Kok|Kong|Kwa|Kwan|"
    "Kwek|Kwok|Lai|Lam|Lau|Lee|Leong|Leow|Li|Liang|Liew|Lim|Lin|Liu|Loh|Loke|Loo|Low|Lui|Mah|Neo|Ng|Ong|Ooi|Pang|Peh|"
    "Phua|Png|Poh|Quah|Quek|Seah|Seet|Seow|Sim|Sng|Soh|Soo|Tan|Tang|Tay|Tee|Teh|Teng|Teo|Tham|Toh|Tong|Wang|Wee|Wong|"
    "Woo|Wu|Xu|Yang|Yap|Yeo|Yeoh|Yip|Yong|Zhang|Zhao|Zhou|Zhu")
_FAMILY = (  # Malay, Indian, Eurasian and common Western family names
    "Abdullah|Hamid|Hassan|Hussain|Ibrahim|Idris|Ismail|Jamal|Karim|Latif|Musa|Omar|Osman|Rahim|Rahman|Rashid|Razak|"
    "Roslan|Salleh|Sulaiman|Yaacob|Yusof|Chandran|Das|Devi|Gill|Govindasamy|Gupta|Iyer|Kaur|Krishnan|Kumar|Menon|"
    "Muthu|Naidu|Nair|Pandian|Patel|Pillai|Rajan|Raman|Ramasamy|Rao|Reddy|Sharma|Singh|Subramaniam|D'Cruz|D'Souza|"
    "Fernandes|Fernandez|Gomes|Lopez|Oliveiro|Pereira|Rodrigues|Rozario|Sequeira|Silva|Souza|Adams|Anderson|Baker|"
    "Bennett|Brown|Carter|Clark|Clarke|Collins|Cooper|Davies|Davis|Edwards|Evans|Garcia|Harrison|Hughes|Johnson|"
    "Jones|Kelly|Lewis|Martin|Miller|Mitchell|Morris|Murphy|Nelson|Nguyen|Parker|Phillips|Roberts|Robinson|Scott|"
    "Smith|Stewart|Taylor|Thompson|Turner|Walker|Watson|Williams|Wilson|Wright")

GUARD_RULES: List[Tuple[str, Pattern[str], str]] = [
    # Patronymics: "Ahmad Danial bin Yusof", "Mdm Siti binte Omar", "Ravi s/o Kumar". First, so a title in front
    # does not split the name.
    ("name", re.compile(rf"\b{_NW}(?:[ \t]+{_NW}){{0,3}}[ \t]+(?i:bin|binte|binti|bte|bt|s/o|d/o|a/l|a/p)[ \t]+"
                        rf"(?:{_NW}|{_INITIAL})(?:[ \t]+{_NW}){{0,2}}"), "[NAME]"),
    # A title, then the name (the first word may be lower case: "mr tan").
    ("name", re.compile(rf"\b(?i:mr|mrs|ms|mdm|madam|madame|mister|dr|encik|cik|puan|tuan)\.?[ \t]+"
                        rf"(?:{_NW}|[a-z][a-z'’-]+|{_INITIAL})(?:[ \t]+{_NW}){{0,3}}"), "[NAME]"),
    # Street names. Run before the name-list rules so "Ang Mo Kio Ave 3" is an address, not a surname.
    ("address", re.compile(rf"\b(?i:jalan|lorong)[ \t]+(?:\d{{1,3}}[A-Za-z]?[ \t]+)?[A-Za-z][a-z'’-]+"
                           rf"(?:[ \t]+{_STREET_WORD_ANY}){{0,2}}|\b(?:Jln|Lor|Lengkok|Lengkong|Kampong|Kg)[ \t]+"
                           rf"(?:\d{{1,3}}[A-Za-z]?[ \t]+)?[A-Z][a-z'’-]+(?:[ \t]+[A-Z][a-z'’-]+){{0,2}}"), "[ADDRESS]"),
    ("address", re.compile(rf"\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}"
                           rf"(?i:road|rd|street|avenue|ave|crescent|cres|boulevard|blvd)\b\.?(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"),
     "[ADDRESS]"),
    ("address", re.compile(rf"\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_TITLE}[ \t]+){{1,4}}"
                           rf"(?:Drive|Lane|Close|Walk|Way|Place|Terrace|Link|Rise|Loop|Circle|Grove|Heights|Hill|Park|"
                           rf"View|Quay|Square|Central|Gardens?|Estate|Green|Vale|St|Pl|Ln|Sq|Dr(?=[ \t]+\d))\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"), "[ADDRESS]"),
    # "my name is jane tan" / "Name: jane": the strongest cues, so lower-case names are taken too (max 2 words).
    ("name", re.compile(r"(\b(?i:my name is|my name's|name is|name\s*:)\s*)[A-Za-z][a-z'’-]*"
                        r"(?:[ \t]+(?!(?i:and|but|i|my|from|at|of|the|here|order)\b)[A-Za-z][a-z'’-]*)?"), r"\1[NAME]"),
    # A cue word, then a Title-case name: "Regards,\nJane", "Dear Priya", "Customer: Tan Ah Kow".
    ("name", re.compile(rf"(\b(?i:(?:i am|i'm|this is|regards|thanks|thank you|cheers|sincerely|faithfully|truly|"
                        rf"best wishes|dear|hi|hello|hey|attn|attention|customer|recipient|received by|signed by|"
                        rf"contact person|sender|consignee|addressee)\b|from[ \t]*:)[\s,:-]*){_NOT_NAME_LA}"
                        rf"{_NW}(?:[ \t]+{_NW}){{0,3}}"), r"\1[NAME]"),
    # Known given name, plus any surname words after it: "Jane", "Jane Tan", "Muhammad Hafiz", "Ryan D".
    ("name", re.compile(rf"\b(?:{_GIVEN})\b(?:[ \t]+{_NW}){{0,3}}(?:[ \t]+{_INITIAL})?"), "[NAME]"),
    # Chinese order, surname first: "Tan Mei Ling", "Ng Chee Keong".
    ("name", re.compile(rf"\b(?:{_SURNAME})[ \t]+{_NW}(?:[ \t]+{_NW}){{0,2}}"), "[NAME]"),
    # Any Title-case word(s) before a known surname or family name: "Xavier Lim", "Kavitha Subramaniam".
    ("name", re.compile(rf"\b{_NOT_NAME_LA}{_NW}(?:[ \t]+{_NW}){{0,2}}[ \t]+(?:{_SURNAME}|{_FAMILY})\b"), "[NAME]"),
]
_RUNS = re.compile(r"\[(NAME|ADDRESS)\](?:[ \t]+\[\1\])+")


def privacy_guard(text: str) -> Tuple[str, Dict[str, int]]:
    """The full guard for text that will leave the machine: mask_text rules, then street addresses and personal names.

    Idempotent (guarding guarded text changes nothing), so it is safe to apply at every layer. Returns
    (guarded_text, counts per rule) like mask_text.
    """
    text, counts = mask_text(text or "")
    text = _apply(GUARD_RULES, text, counts)
    return _RUNS.sub(lambda m: f"[{m.group(1)}]", text), counts
