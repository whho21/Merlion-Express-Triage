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
    ("postal", re.compile(r"(?<![\w$])(?:(?:S|(?i:singapore))\s?)?\d{6}(?!\d)"), "[POSTAL]"),
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
# "Tampines St 11", "Ang Mo Kio Central", "Jalan Bukit Merah"). Names and numbered addresses are caught in Title Case,
# ALL CAPS and lower case (PR #14 review P1). It can MISS an uncommon name with no title or cue (e.g. a lone foreign
# first name, or "zhi wei tan" all in lower case), so the default embedder stays local (nothing leaves the machine).
# Complaint wording, order numbers, driver codes, dates and amounts are left alone so retrieval still works: a typed
# complaint after "Hi," ("Hi, Lat Parcle Apolgy") is not a name (PR #14 review P2).

_NW = r"(?:[A-Z]['’])?[A-Z][a-z]+(?:['’][A-Z]?[a-z]+)?(?:-[A-Z]?[a-z]+)?"  # Title-case word: Tan, D'Cruz, Mary-Ann
_NWU = r"(?:[A-Z]['’])?[A-Z]{2,}(?:['’][A-Z]+)?(?:-[A-Z]+)?"               # ALL-CAPS word: TAN, D'CRUZ
_NWL = r"[a-z]+(?:['’][a-z]+)?(?:-[a-z]+)?"                                 # lower-case word: tan, d'cruz
_WORD = r"(?:[A-Za-z]['’])?[A-Za-z][A-Za-z'’-]*"                            # any casing
_INITIAL = r"[A-Z](?![\w'’])"                                               # a trailing initial: "Ryan D"

# Words that are never taken as (part of) a name, whatever their casing: function words, greetings, titles, verbs a
# name is often followed by, and the complaint vocabulary (so "Hi, Late Delivery" or "mr tan said" keep their words).
_NOT_NAME = (
    "the|a|an|i|we|you|he|she|it|they|this|that|these|those|my|your|our|his|her|their|its|me|us|them|all|both|"
    "everyone|everybody|anyone|someone|guys|folks|team|sir|madam|valued|again|very|so|not|still|here|there|please|"
    "sorry|regards|thanks|thank|hope|good|morning|afternoon|evening|night|kind|best|warm|yours|re|fw|fwd|subject|to|"
    "from|cc|bcc|on|in|at|of|for|and|or|but|if|when|why|how|what|who|whose|whom|which|where|with|about|regarding|"
    "because|since|as|by|up|down|out|over|into|onto|than|via|per|vs|etc|is|was|are|were|be|been|am|has|had|have|"
    "did|does|do|will|would|can|could|should|may|might|must|no|yes|ok|okay|hi|hello|hey|dear|mr|mrs|ms|mdm|dr|"
    "also|already|just|only|even|then|now|today|yesterday|tomorrow|anyway|anyways|"
    "said|says|say|told|tells|tell|called|calls|call|wants|want|asked|asks|ask|came|come|went|got|get|gave|give|"
    "sent|send|took|take|made|make|needs|need|wrote|writes|write|writing|complained|complains|reported|reports|"
    "requested|requests|claimed|claims|refused|refuses|signed|signs|lives|live|stays|stay|works|work|ordered|"
    "unacceptable|ridiculous|disappointing|disappointed|frustrated|angry|upset|unhappy|happy|shocked|annoyed|"
    "furious|extremely|really|truly|totally|absolutely|completely|quite|rather|too|most|more|less|much|many|some|"
    "any|every|each|another|other|such|same|different|first|second|third|last|next|previous|new|old|big|small|"
    "late|lat|delay|delayed|delivery|deliveries|delivered|deliver|parcel|parcels|package|packages|item|items|order|"
    "orders|refund|refunds|damaged|damage|broken|broke|smashed|cracked|dented|torn|wet|missing|lost|stolen|gone|"
    "empty|opened|open|arrived|arrive|wrong|right|bad|poor|terrible|rude|nice|helpful|polite|friendly|fast|slow|"
    "quick|early|address|block|unit|cash|cod|pod|amount|overcharge|charge|charged|driver|drivers|complaint|"
    "complaints|complain|apology|apologies|apologise|apologize|urgent|issue|issues|problem|problems|help|status|"
    "update|query|question|request|enquiry|inquiry|feedback|claim|compensation|gate|thrown|threw|left|outside|"
    "door|neighbour|neighbor|received|receive|never|week|month|day|days|time|times|fee|fees|payment|paid|pay|"
    "invoice|receipt|tracking|track|number|ref|reference|merchant|customer|customers|service|services|support|cs|"
    "public|holiday|weight|kg|zone|zones|central|north|south|east|west|singapore|merlion|express|cbd|gps|nric|sg|"
    "sgd|usd|asap|fyi|id|pm|hdb|mrt|pdpa|api|faq|eta|tbc|tba|na|drv|merl|name|email|phone|postal|card|quality|"
    "packaging|battery|priority|cost|level|price|prices|band|limit|box|boxes")
_NOT_NAME_LA = rf"(?!(?i:{_NOT_NAME})\b)"
_NAMEWORD = rf"{_NOT_NAME_LA}(?:{_NW}|{_NWU})"   # Title or CAPS, not an excluded word
_LNAME = rf"{_NOT_NAME_LA}{_NWL}"                 # lower case, not an excluded word
_ANYNAME = rf"{_NOT_NAME_LA}{_WORD}"              # any casing, not an excluded word
_CAPSNAME = rf"{_NOT_NAME_LA}{_NWU}"
_SHORTLOW = rf"{_NOT_NAME_LA}[a-z]{{2,6}}\b"      # a lower-case Chinese given-name syllable: mei, ling, kuan, yew
_SHORTCAPS = rf"{_NOT_NAME_LA}[A-Z]{{2,6}}\b"     # the same in CAPS: MEI, LING, AH, KOW
_SHORTTITLE = rf"{_NOT_NAME_LA}[A-Z][a-z]{{1,5}}(?:-[A-Z]?[a-z]{{1,5}})?\b"  # Mei, Ling, Guo, Hwee, Mei-Ling
_PARTICLE = r"(?i:de|da|del|dos|van|von)"         # "Clara de Silva"

# Words that may precede a street suffix but are not part of a street name (case-insensitive). Directions
# ("Bedok North Drive") and "Central" are street words, so they are NOT in this list.
_NOT_STREET = ("the|a|an|my|your|our|his|her|their|its|this|that|these|those|at|on|in|to|of|from|for|near|via|by|and|"
               "or|but|is|was|are|were|be|been|along|down|up|across|over|off|main|same|wrong|right|other|next|another|"
               "any|no|not|which|what|private|public|side|busy|old|new|whole|entire|every|each|one|two|three|first|"
               "second|third|last|nearest|more|only|better|easy|"
               "late|delay|delayed|delivery|delivered|deliver|parcel|parcels|package|packages|item|items|order|orders|"
               "refund|damaged|damage|broken|missing|lost|cash|cod|pod|amount|driver|drivers|complaint|complaints|"
               "apology|urgent|issue|problem|help|status|update|gate|thrown|threw|left|outside|door|neighbour|neighbor|"
               "received|never|week|month|day|days|time|times|fee|payment|paid|tracking|number|merchant|customer|"
               "service|support|team|regards|thanks|hi|hello|dear|mr|mrs|ms|mdm|dr|kg|zone|weight|holiday|hour|hours|"
               "minute|minutes|star|stars|attempt|attempts|wait|waited|waiting|go|going|went|get|got|find|found|take|"
               "took|long")
_STREET_WORD_ANY = rf"(?!(?i:{_NOT_STREET})\b)[A-Za-z][A-Za-z'’-]*"
_STREET_WORD_TITLE = rf"(?!(?i:{_NOT_STREET})\b)[A-Z][a-z'’-]+"
_STREET_WORD_CAPS = rf"(?!(?i:{_NOT_STREET})\b)[A-Z][A-Z'’-]+"
_SUFFIX_T = (r"Drive|Lane|Close|Walk|Way|Place|Terrace|Link|Rise|Loop|Circle|Grove|Heights|Hill|Park|View|Quay|Square|"
             r"Central|Gardens?|Estate|Green|Vale|St|Pl|Ln|Sq|Dr(?=[ \t]+\d)")
_SUFFIX_U = (r"DRIVE|LANE|CLOSE|WALK|WAY|PLACE|TERRACE|LINK|RISE|LOOP|CIRCLE|GROVE|HEIGHTS|HILL|PARK|VIEW|QUAY|SQUARE|"
             r"CENTRAL|GARDENS?|ESTATE|GREEN|VALE|ST|PL|LN|SQ|DR(?=[ \t]+\d)")
_SUFFIX_ANY = (r"drive|lane|close|walk|way|place|terrace|link|rise|loop|circle|grove|heights|hill|park|view|quay|square|"
               r"central|gardens?|estate|green|vale|st|pl|ln|sq|dr(?=[ \t]+\d|[ \t]*$|[.,;:)])")
_SUFFIX_ALL = (r"road|rd|street|avenue|ave|crescent|cres|boulevard|blvd|drive|lane|close|walk|way|place|terrace|link|"
               r"rise|loop|circle|grove|heights|hill|park|view|quay|square|central|gardens?|estate|green|vale|st|pl|ln|"
               r"sq|dr")
# Singapore towns and estates (the 19 in the client data plus the other HDB towns). A town word followed by a street
# suffix is an address whatever the casing: "bedok central", "toa payoh st 11". A town alone ("Bedok") is left, so
# zone questions still work.
_TOWN = ("Ang Mo Kio|Bedok|Bishan|Bukit Batok|Bukit Merah|Bukit Panjang|Bukit Timah|Choa Chu Kang|Clementi|Geylang|"
         "Hougang|Jurong East|Jurong West|Jurong|Kallang|Marine Parade|Pasir Ris|Punggol|Queenstown|Sembawang|Sengkang|"
         "Serangoon|Tampines|Toa Payoh|Woodlands|Yishun|Novena|Tanglin|Orchard|Tengah|Boon Lay|Bukit Gombak|"
         "Telok Blangah|Tiong Bahru|Whampoa|Balestier|Redhill|Potong Pasir|Macpherson|Ubi|Eunos|Kembangan|"
         "Bedok Reservoir|Simei|Changi|Loyang|Compassvale|Rivervale|Anchorvale|Fernvale|Buangkok|Kovan|Upper Thomson|"
         "Thomson|Sin Ming|Marsiling|Admiralty|Canberra|Khatib|Chong Pang|Teck Whye|Yew Tee|Keat Hong|Taman Jurong|"
         "Ghim Moh|Buona Vista|Kent Ridge|Pasir Panjang|Havelock|Kim Tian|Boon Keng|Bugis|Rochor|Kallang Bahru|"
         "Aljunied|Paya Lebar|Tai Seng|Bartley|Yio Chu Kang|Lentor|Mayflower|Springleaf|Woodleigh|Marymount|Braddell|"
         "Caldecott|Punggol Field|Sengkang East|Sengkang West|Tampines North|Woodlands South|Yishun Ring|Siglap|Katong|"
         "Joo Chiat|Mountbatten|Dakota|Stadium|Nicoll|Beach|Shenton|Raffles|Cantonment|Outram|Chinatown|Clarke Quay|"
         "Boat Quay|Robertson Quay|River Valley|Newton|Stevens|Botanic|Farrer Park|Little India|Kampong Glam")
_TOWN_WORDS = tuple(sorted({w for t in _TOWN.split("|") for w in t.split()}, key=str.lower))

_GIVEN = (  # common given names in Singapore; English words that are also names (May, Will, Grace ...) left out
    "Aaron|Abdul|Adam|Adrian|Agnes|Ahmad|Aisyah|Alan|Alex|Alexander|Alice|Alicia|Alvin|Amanda|Amir|Aminah|Amy|Anand|"
    "Andrew|Andy|Angela|Angeline|Anita|Anitha|Ann|Anna|Anne|Anthony|Arjun|Arun|Ashley|Audrey|Azman|Benjamin|Benny|"
    "Bernard|Bryan|Calvin|Candice|Carol|Catherine|Charles|Charlene|Cheryl|Christina|Christine|Christopher|Cindy|Clara|"
    "Clarence|Daniel|Darren|Daryl|David|Deepa|Dennis|Derek|Desmond|Divya|Dominic|Edmund|Edwin|Elaine|Eleanor|Elizabeth|"
    "Emily|Eric|Esther|Eugene|Evelyn|Farah|Faridah|Farhan|Felicia|Fiona|Gabriel|Ganesh|Gary|Geraldine|Germaine|Gerald|"
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
    "Muthu|Naidu|Nair|Pandian|Patel|Pillai|Rajan|Raman|Ramasamy|Rao|Reddy|Sharma|Singh|Subramaniam|D['’]Cruz|"
    "D['’]Souza|Fernandes|Fernandez|Gomes|Lopez|Oliveiro|Pereira|Rodrigues|Rozario|Sequeira|Silva|Souza|Adams|Anderson|"
    "Baker|Bennett|Brown|Carter|Clark|Clarke|Collins|Cooper|Davies|Davis|Edwards|Evans|Garcia|Harrison|Hughes|Johnson|"
    "Jones|Kelly|Lewis|Martin|Miller|Mitchell|Morris|Murphy|Nelson|Nguyen|Parker|Phillips|Roberts|Robinson|Scott|"
    "Smith|Stewart|Taylor|Thompson|Turner|Walker|Watson|Williams|Wilson|Wright")
_KNOWN_I = rf"(?i:{_SURNAME}|{_FAMILY}|{_GIVEN})\b"   # any known name word, any casing
_TITLE = r"(?i:mr|mrs|ms|mdm|madam|madame|mister|dr|encik|cik|puan|tuan)"

GUARD_RULES: List[Tuple[str, Pattern[str], str]] = [
    # Patronymics: "Ahmad Danial bin Yusof", "Mdm Siti binte Omar", "Ravi s/o Kumar", "ahmad bin yusof". First, so a
    # title in front does not split the name.
    ("name", re.compile(rf"\b(?:{_TITLE}\.?[ \t]+)?{_ANYNAME}(?:[ \t]+{_ANYNAME}){{0,3}}[ \t]+"
                        rf"(?i:bin|binte|binti|bte|bt|s/o|d/o|a/l|a/p)"
                        rf"[ \t]+(?:{_ANYNAME}|{_INITIAL})(?:[ \t]+(?:{_NAMEWORD}|{_KNOWN_I})){{0,2}}"), "[NAME]"),
    # A title, then the name in any casing: "Mr Tan", "Mr TAN AH KOW", "mr tan ah kow".
    ("name", re.compile(rf"\b{_TITLE}\.?[ \t]+"
                        rf"(?:{_NAMEWORD}(?:[ \t]+{_NAMEWORD}){{0,3}}|{_LNAME}(?:[ \t]+{_LNAME}){{0,2}}|{_INITIAL})"),
     "[NAME]"),
    # Street names. Run before the name-list rules so "Ang Mo Kio Ave 3" is an address, not a surname.
    ("address", re.compile(rf"\b(?i:jalan|lorong|jln)[ \t]+(?:\d{{1,3}}[A-Za-z]?[ \t]+)?{_STREET_WORD_ANY}"
                           rf"(?:[ \t]+{_STREET_WORD_ANY}){{0,2}}"
                           rf"|(?<!\d[ \t])\b(?:Lor|LOR|Lengkok|LENGKOK|Lengkong|LENGKONG|Kampong|KAMPONG|Kg|KG)[ \t]+"
                           rf"(?:\d{{1,3}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_TITLE}|{_STREET_WORD_CAPS})"
                           rf"(?:[ \t]+(?:{_STREET_WORD_TITLE}|{_STREET_WORD_CAPS})){{0,2}}"), "[ADDRESS]"),
    ("address", re.compile(rf"\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}"
                           rf"(?i:road|rd|street|avenue|ave|crescent|cres|boulevard|blvd)\b\.?(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"),
     "[ADDRESS]"),
    # Drive/Lane/Way/...: these suffixes are everyday words, so without a house number the words must be Title Case
    # (or ALL CAPS); with a house number in front any casing counts ("12 bedok north drive").
    ("address", re.compile(rf"\b\d{{1,4}}[A-Za-z]?[ \t]+(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}(?i:{_SUFFIX_ANY})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"
                           rf"|\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_TITLE}[ \t]+){{1,4}}(?:{_SUFFIX_T})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"
                           rf"|\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_CAPS}[ \t]+){{1,4}}(?:{_SUFFIX_U})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"), "[ADDRESS]"),
    # A known town followed by a street suffix, any casing: "bedok central", "TOA PAYOH ST 11", "bukit batok drive".
    ("address", re.compile(rf"\b(?i:{_TOWN})\b(?:[ \t]+{_STREET_WORD_ANY}){{0,2}}[ \t]+(?i:{_SUFFIX_ALL})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"), "[ADDRESS]"),
    # A street suffix followed by its number is an address in any casing: "bedok st 11", "clementi ave 4", "yishun dr 1".
    ("address", re.compile(rf"\b(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}(?i:st|street|ave|avenue|dr|drive|rd|road|lane|ln|"
                           rf"walk|link|close|cres|crescent)[ \t]+\d{{1,3}}[A-Za-z]?\b"), "[ADDRESS]"),
    # Words between a masked block number and a street suffix, or before a masked unit / postal code, any casing:
    # "blk [BLOCK] bedok drive [UNIT]".
    ("address", re.compile(rf"(\[BLOCK\][ \t]+)(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}(?i:{_SUFFIX_ALL})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?"), r"\1[ADDRESS]"),
    ("address", re.compile(rf"\b(?:\d{{1,4}}[A-Za-z]?[ \t]+)?(?:{_STREET_WORD_ANY}[ \t]+){{1,4}}(?i:{_SUFFIX_ALL})\b\.?"
                           rf"(?:[ \t]+\d{{1,3}}[A-Za-z]?\b)?(?=[ \t]*(?:#|\[UNIT\]|\[POSTAL\]))"), "[ADDRESS]"),
    # Field cues: the strongest signal, so any casing is taken, up to 4 words: "my name is jane tan", "Customer: JANE
    # TAN", "From: Daniel Souza", "Name: tan ah kow".
    ("name", re.compile(rf"(\b(?i:my name is|my name's|name is|name\s*:|customer\s*:|recipient\s*:|consignee\s*:|"
                        rf"addressee\s*:|sender\s*:|contact person\s*:|contact\s*:|attn\s*:|attention\s*:|from\s*:|"
                        rf"signed by|received by)\s*){_ANYNAME}(?:[ \t]+{_ANYNAME}){{0,3}}"), r"\1[NAME]"),
    # A cue word, then a Title-case or CAPS name: "Regards,\nJane", "Dear Priya", "Customer Tan Ah Kow", "Regards, JOHN".
    ("name", re.compile(rf"(\b(?i:i am|i'm|this is|regards|thanks|thank you|cheers|sincerely|faithfully|truly|"
                        rf"best wishes|dear|attn|attention|customer|recipient|received by|signed by|contact person|"
                        rf"sender|consignee|addressee)\b[\s,:-]*){_NAMEWORD}(?:[ \t]+{_NAMEWORD}){{0,3}}"), r"\1[NAME]"),
    # Sign-offs and "dear" followed by a lower-case name: "regards, jane tan", "dear priya".
    ("name", re.compile(rf"(\b(?i:regards|thanks|thank you|cheers|sincerely|faithfully|dear)\b[\s,:-]*)"
                        rf"{_LNAME}(?:[ \t]+{_LNAME}){{0,2}}"), r"\1[NAME]"),
    # Greetings are a weak cue (PR #14 review P2): at most two Title/CAPS words, and only when a comma, full stop,
    # line break or the end of the text follows, as in "Hi Jane," / "Hello Zhi Wei\n". "Hi, Lat Parcle Apolgy" and
    # "Hi, Late Delivery" are complaint text and stay.
    ("name", re.compile(rf"(\b(?i:hi|hello|hey)\b[ \t,]*){_NAMEWORD}(?:[ \t]+{_NAMEWORD})?(?=[ \t]*(?:[,.!?;:]|\r?\n|$))"),
     r"\1[NAME]"),
    # Title-case word(s) before a known surname or family name, plus any name words after: "Xavier Lim",
    # "Kavitha Subramaniam", "Lim Jane Tan". Before the given-name rule so the whole name goes in one piece.
    ("name", re.compile(rf"\b{_NAMEWORD}(?:[ \t]+(?:{_NAMEWORD}|{_PARTICLE})){{0,2}}[ \t]+(?:{_SURNAME}|{_FAMILY})\b"
                        rf"(?:[ \t]+{_NAMEWORD}){{0,2}}"), "[NAME]"),
    # Known given name, plus any name words after it: "Jane", "Jane Tan", "Jane tan", "Muhammad Hafiz", "Ryan D".
    ("name", re.compile(rf"\b(?:{_GIVEN})\b(?:[ \t]+(?:{_NAMEWORD}|{_KNOWN_I}|{_PARTICLE}[ \t]+{_KNOWN_I})){{0,3}}"
                        rf"(?:[ \t]+{_INITIAL})?"), "[NAME]"),
    # Chinese order, surname first: "Tan Mei Ling", "Ng Chee Keong".
    ("name", re.compile(rf"\b(?:{_SURNAME})[ \t]+(?:{_KNOWN_I}|{_SHORTTITLE})(?:[ \t]+(?:{_KNOWN_I}|{_SHORTTITLE})){{0,2}}"),
     "[NAME]"),
    # ALL CAPS: "ZHI WEI TAN", "JANE TAN", "TAN AH KOW"; lower case: "jane tan", "tan mei ling", "lim jane".
    ("name", re.compile(rf"\b{_CAPSNAME}(?:[ \t]+{_CAPSNAME}){{0,2}}[ \t]+(?i:{_SURNAME}|{_FAMILY})\b"
                        rf"(?:[ \t]+{_CAPSNAME}){{0,2}}"), "[NAME]"),
    ("name", re.compile(rf"\b(?i:{_SURNAME})\b[ \t]+(?:(?i:{_GIVEN})\b(?:[ \t]+{_KNOWN_I}){{0,2}}"
                        rf"|{_SHORTLOW}[ \t]+{_SHORTLOW}(?:[ \t]+{_SHORTLOW})?"
                        rf"|{_SHORTCAPS}[ \t]+{_SHORTCAPS}(?:[ \t]+{_SHORTCAPS})?)"), "[NAME]"),
    ("name", re.compile(rf"\b(?i:{_GIVEN})\b(?:[ \t]+(?:{_KNOWN_I}|{_CAPSNAME}|{_PARTICLE}[ \t]+{_KNOWN_I})){{0,3}}"),
     "[NAME]"),
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
