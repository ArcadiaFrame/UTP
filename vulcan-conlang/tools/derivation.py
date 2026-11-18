"""Word-building table: which meanings are roots and which are built from older words.

Basis, in order of authority:
  1. Canon Vulcan patterns (the model for every process here):
       -tor "do, make" as a verb-maker (dif-tor "live long"), ve "one, person" (ish-ve, nash-ve),
       kau "joined, together" (kash-kau), -ik participle (seheik "declared"), -kam diminutive,
       noun-noun compounds (plak tow, pon far, koon-ut, kas-wan), and "mik t'X" "inquiry of X".
  2. Anthropology and evolutionary linguistics: the oldest, most stable meanings are roots
     (basic body, kin, nature, motion and emotion vocabulary, as in the Swadesh and Leipzig-Jakarta
     lists); colour terms arrive in the Berlin-Kay order; social, institutional, abstract and
     technical meanings are built later from older roots, by metaphor drawn from Vulcan life.
  3. English, Latin and Japanese as cross-checks: where two of the three build a meaning from
     another word, Vulcan does too, using its own pieces.

Each entry: key -> (parts, basis). Parts use {key} for a word and + (fused) or - (hyphen) to join.
A part may name another derived key; expand() resolves it down to roots.
Later batches add rows to lexicon/derivations.csv instead of editing this table.
Run: python3 tools/derivation.py   (rewrites lexicon/meanings.csv, then run lexicon.py build)
"""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ERA_RANK = {"Tribal": 0, "Classical": 1, "Unified": 2, "Standard": 3, "Romulan": 3}

# ---- new derivational endings (generated like any root; era says when each became productive) ----
NEW_AFFIXES = [
    # key, gloss, pos, era, notes
    ("action", "action noun (suffix: the act or its outcome)", "suffix", "Classical",
     "Latin -tio, English -tion/-ment, Japanese koto/-mono. Turns a verb into a noun"),
    ("place-suf", "place (suffix: where something is done or kept)", "suffix", "Classical",
     "Latin -orium/-arium, Japanese -jo/-kan/-ba, English -ery"),
    ("instrument", "instrument (suffix: the thing used to do it)", "suffix", "Classical",
     "Latin -trum/-culum, Japanese -ki/-gu"),
    ("collective", "collective (suffix: a body of, a group of)", "suffix", "Classical",
     "Latin -tus/-itas in coetus, Japanese -dan/-shu, English -ship/-ry"),
    ("indef", "indefinite (suffix on a question word: some-)", "suffix", "Classical",
     "Japanese dare-ka 'someone' from dare 'who'; Latin ali-quis; the commonest pattern in the world's languages (Haspelmath)"),
    ("univ", "universal (suffix on a question word: every-)", "suffix", "Classical",
     "Japanese dare-mo 'everyone'; Latin quis-que"),
]

D = {
    # ---------- function words: indefinites built from question words (Japanese, Latin, typology) ----------
    "someone": ("{who}+{indef}", "who + some-: JA dare-ka, LA ali-quis"),
    "something": ("{what}+{indef}", "what + some-: JA nani-ka, LA ali-quid"),
    "somewhere": ("{where}+{indef}", "where + some-: JA doko-ka, LA ali-cubi"),
    "sometimes": ("{when}+{indef}", "when + some-: JA itsu-ka, LA ali-quando"),
    "everyone": ("{who}+{univ}", "who + every-: JA dare-mo, LA quis-que"),
    "everything": ("{what}+{univ}", "what + every-: JA nan-demo"),
    "everywhere": ("{where}+{univ}", "where + every-: JA doko-demo, LA ubi-que"),
    "nothing": ("{not}-{thing}", "not + thing: LA ni-hil, EN no-thing"),
    "nowhere": ("{not}-{place}", "not + place: EN no-where"),
    "how-many": ("{how}-{many}", "how + many: JA iku-tsu"),
    "each-other": ("{one}-{other}", "one + other: LA alter alterum"),
    "together": ("{kau}+{adverbial}", "canon kau 'joined, together' + -ly"),
    "finally": ("{end}+{adverbial}", "end + -ly: LA finaliter, JA tsui-ni"),
    "later": ("{after}+{adverbial}", "after + -ly: JA ato-de, EN late-r"),
    "usually": ("{common}+{adverbial}", "common + -ly: LA vulgo"),
    # ---------- colour: Berlin-Kay order; later colours named from things in Vulcan life ----------
    "green": ("{plak}+{adjectival}", "culture: Vulcan blood is green, so green is 'blood-coloured'. Stage IV colour, Classical"),
    "yellow": ("{sun}+{adjectival}", "sun-coloured. Stage III-IV colour"),
    "blue": ("{void}+{adjectival}", "culture: Vulcan's sky is pale and red; blue is the colour of the deep void at dusk. Stage V colour, late"),
    "brown": ("{sand}+{adjectival}", "sand-coloured (canon mazhiv). Stage VI colour, late"),
    # ---------- adjectives built from nouns and verbs ----------
    "hungry": ("{hunger}+{adjectival}", "hunger + -y: JA ue-ta, EN hungr-y"),
    "thirsty": ("{thirst}+{adjectival}", "thirst + -y"),
    "spicy": ("{spice}+{adjectival}", "spice + -y"),
    "dangerous": ("{danger}+{adjectival}", "LA periculosus, EN danger-ous"),
    "useful": ("{use}+{adjectival}", "LA utilis < uti, EN use-ful"),
    "famous": ("{name}+{adjectival}", "LA famosus < fama; JA yuu-mei 'having a name'"),
    "healthy": ("{health}+{adjectival}", "EN health-y, JA kenkou-na"),
    "possible": ("{kup}+{adjectival}", "canon kup 'can' + -uk: LA possibilis < posse, JA ka-nou"),
    "impossible": ("{without}-{kup}+{adjectival}", "without + possible: LA im-possibilis, JA fu-kanou"),
    "necessary": ("{need}+{adjectival}", "LA necessarius, JA hitsu-you"),
    "acceptable": ("{accept}+{adjectival}", "LA acceptabilis"),
    "familiar": ("{family}+{adjectival}", "LA familiaris < familia, EN familiar"),
    "modern": ("{now}+{adjectival}", "LA modernus < modo 'just now', JA gen-dai 'present age'"),
    "temporary": ("{pon}+{adjectival}", "canon pon 'time' + -uk: LA temporarius < tempus"),
    "permanent": ("{always}+{adjectival}", "always + -uk: JA eien-no"),
    "partial": ("{part}+{adjectival}", "LA partialis"),
    "local": ("{place}+{adjectival}", "LA localis < locus"),
    "public": ("{people-n}+{adjectival}", "LA publicus < populus"),
    "private": ("{self}+{adjectival}", "JA shi-teki 'of the self'"),
    "personal": ("{person}+{adjectival}", "canon banut + -uk: LA personalis"),
    "formal-a": ("{propriety}+{adjectival}", "of propriety: JA sei-shiki"),
    "essential": ("{essence}+{adjectival}", "LA essentialis"),
    "optional": ("{choice}+{adjectival}", "LA optio + -alis"),
    "reasonable": ("{reason}+{adjectival}", "LA rationabilis, EN reason-able"),
    "serious": ("{heavy}+{adjectival}", "metaphor heavy = grave: LA gravis, JA juu-dai"),
    "polite": ("{courtesy}+{adjectival}", "JA rei-gi tadashii 'correct in courtesy'"),
    "rude": ("{without}-{courtesy}", "without courtesy: JA shitsu-rei 'lost courtesy', LA in-civilis"),
    "foreign": ("{outside}+{adjectival}", "LA externus, JA gai-koku 'outside country'"),
    "emotional": ("{emotion}+{adjectival}", "EN emotion-al"),
    "innocent": ("{without}-{crime}", "without crime: JA mu-zai, LA in-nocens"),
    "guilty": ("{crime}+{adjectival}", "JA yuu-zai 'having crime'"),
    "barren": ("{without}-{seed}", "without seed: JA fu-mou 'without growth'"),
    "fertile": ("{seed}+{adjectival}", "seed + -uk: LA fertilis < ferre"),
    "stormy": ("{storm}+{adjectival}", "canon takak + -uk"),
    "dusty": ("{dust}+{adjectival}", ""),
    "rocky": ("{stone}+{adjectival}", ""),
    "windy": ("{wind}+{adjectival}", ""),
    "humid": ("{water}+{adjectival}", "watery: LA umidus"),
    "scorching": ("{heat}+{participle-ik}", "heated, with canon -ik"),
    "glowing": ("{far}+{participle-ik}", "canon far 'fire' + -ik: kindled"),
    "alone": ("{one}-{ve}", "one + canon ve 'person': JA hitori 'one person', EN all-one"),
    "first": ("{one}+{ordinal}", "one + -th: JA dai-ichi"),
    "beloved": ("{love}+{participle-ik}", "loved: LA amatus, JA itoshii"),
    "betrothed": ("{promise}+{participle-ik}", "promised: LA sponsus, the promised one"),
    "unequal": ("{without}-{equal}", "LA in-aequalis, JA fu-byoudou"),
    "adult": ("{grow}+{participle-ik}", "grown: LA adultus, the participle of adolescere"),
    # ---------- abstract nouns from adjectives (-hol, Unified: Surak's philosophers coined them) ----------
    "wisdom": ("{wise}+{abstract}", "LA sapientia < sapiens, JA kashiko-sa, EN wis-dom"),
    "freedom": ("{free}+{abstract}", "LA libertas < liber, EN free-dom"),
    "safety": ("{safe}+{abstract}", "LA salus, EN safe-ty"),
    "simplicity": ("{simple}+{abstract}", "LA simplicitas"),
    "curiosity": ("{curious}+{abstract}", "LA curiositas"),
    "certainty": ("{certain}+{abstract}", "LA certitudo"),
    "loyalty": ("{loyal}+{abstract}", ""),
    "beauty": ("{beautiful}+{abstract}", "the adjective is older: LA pulcher > pulchritudo, JA utsukushi-sa"),
    "illness": ("{ill}+{abstract}", "EN ill-ness"),
    "poverty": ("{poor}+{abstract}", "LA paupertas < pauper"),
    "wealth": ("{rich}+{abstract}", "EN weal-th"),
    "diversity": ("{different}+{abstract}", "LA diversitas"),
    "infinity": ("{without}-{end}", "without end: LA in-finitas, JA mu-gen"),
    "identity": ("{self}+{abstract}", "selfhood: JA ji-ko"),
    "civilization": ("{city}+{abstract}", "LA civilitas < civis, the city"),
    "society": ("{companion}+{abstract}", "LA societas < socius 'companion'"),
    "community": ("{kau}+{abstract}", "canon kau 'joined' + -hol: LA communitas"),
    "mastery": ("{master}+{abstract}", ""),
    "privacy": ("{private}+{abstract}", "a Vulcan value: the state of the self kept to itself"),
    "truth": ("{true}+{abstract}", "LA veritas < verus, JA shin-jitsu"),
    "tenderness": ("{soft}+{abstract}", "LA teneritas < tener"),
    "loneliness": ("{alone}+{abstract}", "EN lone-li-ness"),
    "composure": ("{calm}+{abstract}", ""),
    "authority": ("{rule-v}+{abstract}", "LA auctoritas"),
    "obligation": ("{must}+{abstract}", ""),
    "heritage": ("{ancestors}+{abstract}", "canon orfikkel + -hol"),
    "alliance": ("{ally}+{abstract}", ""),
    "probability": ("{possible}+{abstract}", "LA probabilitas"),
    "gravity": ("{heavy}-{force}", "heavy force: JA juu-ryoku; LA gravitas < gravis"),
    "vacuum": ("{empty}+{abstract}", "LA vacuum < vacuus, JA shin-kuu"),
    "length": ("{long}+{abstract}", "EN length < long, LA longitudo, JA naga-sa"),
    "width": ("{wide}+{abstract}", "EN width < wide, JA haba"),
    "height": ("{high}+{abstract}", "EN height < high, JA taka-sa"),
    "depth": ("{deep}+{abstract}", "EN depth < deep, JA fuka-sa"),
    "weight": ("{heavy}+{abstract}", "EN weight, JA omo-sa"),
    "distance-n": ("{distant}+{abstract}", "LA distantia, JA too-sa"),
    # ---------- action nouns from verbs ----------
    "existence": ("{exist}+{action}", "LA existentia"),
    "failure": ("{fail}+{action}", ""),
    "success": ("{succeed}+{action}", "LA successus"),
    "victory": ("{win}+{action}", "LA victoria < vincere"),
    "defeat": ("{lose}+{action}", ""),
    "agreement": ("{agree}+{action}", ""),
    "negotiation": ("{negotiate}+{action}", "LA negotiatio"),
    "betrayal": ("{betray}+{action}", ""),
    "service": ("{serve}+{action}", "LA servitium"),
    "observation": ("{observe}+{action}", "LA observatio"),
    "decision": ("{decide}+{action}", "LA decisio"),
    "explanation": ("{explain}+{action}", ""),
    "description": ("{describe}+{action}", "LA descriptio"),
    "arrival": ("{arrive}+{action}", ""),
    "departure": ("{depart}+{action}", ""),
    "meeting": ("{meet}+{action}", "EN meet-ing, JA ai"),
    "greeting": ("{greet}+{action}", "EN greet-ing, JA aisatsu"),
    "invitation": ("{invite}+{action}", "LA invitatio"),
    "warning": ("{warn}+{action}", ""),
    "promise-n": ("{promise}+{action}", ""),
    "request-n": ("{ask}+{action}", "an asking"),
    "answer-n": ("{answer}+{action}", ""),
    "discussion": ("{discuss}+{action}", "LA discussio"),
    "argument": ("{argue}+{action}", "LA argumentum < arguere"),
    "instruction": ("{command-v}+{action}", "LA instructio"),
    "conversation": ("{speak}-{kau}+{action}", "speaking joined: LA con-versatio, JA kai-wa 'meeting talk'"),
    "journey": ("{travel}+{action}", ""),
    "performance": ("{perform}+{action}", ""),
    "painting": ("{paint}+{action}", "EN paint-ing"),
    "carving": ("{carve}+{action}", "EN carv-ing"),
    "sculpture": ("{sculpt}+{action}", "LA sculptura"),
    "imagination": ("{imagine}+{action}", "LA imaginatio"),
    "sensation": ("{feel}+{action}", "LA sensatio < sentire"),
    "experience": ("{try}+{action}", "LA experientia < experiri 'to try'"),
    "belief": ("{believe}+{action}", ""),
    "intention": ("{intend}+{action}", "LA intentio"),
    "insight": ("{in}-{see}+{action}", "in + seeing: EN in-sight, LA in-tuitio"),
    "structure": ("{build}+{action}", "LA structura < struere 'build'"),
    "concept": ("{think}+{action}", "LA conceptus"),
    "tradition": ("{give}+{action}", "LA traditio < tradere 'hand over'"),
    "permission": ("{allow}+{action}", "LA permissio"),
    "growth": ("{grow}+{action}", "EN grow-th"),
    "cooperation": ("{work}-{kau}+{action}", "LA co-operatio, JA kyou-ryoku"),
    "injury": ("{injure}+{action}", "LA iniuria"),
    "damage": ("{break}+{action}", "a breaking"),
    "work-n": ("{work}+{action}", ""),
    "question-n": ("{ask}-{question}", "ask + canon-style question particle kuth"),
    "meaning": ("{mean}+{action}", "EN mean-ing"),
    "testimony": ("{witness}+{action}", "LA testimonium < testis"),
    "rule-n": ("{rule-v}+{action}", "LA regula < regere"),
    "trade-n": ("{trade}+{action}", ""),
    "government": ("{govern}+{action}", "EN govern-ment, LA gubernatio"),
    "property": ("{have}+{action}", "what one has: LA proprietas, JA shoyuu-butsu"),
    "measure-n": ("{measure}+{action}", "LA mensura"),
    "equation": ("{equal}+{action}", "LA aequatio < aequare"),
    "election": ("{vote}-{choose}+{action}", "LA electio < eligere 'choose out'"),
    "doctrine": ("{teach}+{action}", "LA doctrina < docere"),
    "tapestry": ("{weave}+{action}", "a weaving"),
    "combination": ("{join}+{action}", "LA combinatio"),
    "decline": ("{fall}+{action}", "LA declinatio"),
    # ---------- persons: canon ve "one, person" (Japanese -sha/-nin, Latin -tor) ----------
    "teacher": ("{teach}-{ve}", "teaching one: JA kyou-shi, LA doc-tor"),
    "builder": ("{build}-{ve}", ""), "hunter": ("{hunt}-{ve}", ""), "cook-n": ("{cook}-{ve}", ""),
    "writer": ("{write}-{ve}", ""), "singer": ("{sing}-{ve}", ""), "traveler": ("{travel}-{ve}", ""),
    "observer": ("{observe}-{ve}", ""), "melder": ("{meld}-{ve}", "ENT 'melder'"),
    "student": ("{learn}-{ve}", "learning one: JA gaku-sei, LA stud-ens"),
    "scientist": ("{inquiry}-{ve}", "inquiry one: JA kagaku-sha"),
    "engineer": ("{machine}-{ve}", "LA ingeniator"),
    "pilot": ("{fly}-{ve}", ""), "soldier": ("{war}-{ve}", "JA hei-shi"), "merchant": ("{trade}-{ve}", "JA shou-nin"),
    "farmer": ("{soil}-{ve}", "LA agri-cola 'field-tiller', JA nou-min"),
    "artist": ("{art}-{ve}", ""), "scholar": ("{knowledge}-{ve}", "JA gaku-sha"),
    "scribe": ("{scroll}-{ve}", "LA scriba"), "miner": ("{dig}-{ve}", ""), "weaver": ("{weave}-{ve}", ""),
    "potter": ("{pottery}-{ve}", ""), "smith": ("{metal}-{ve}", "JA kaji"), "musician": ("{music}-{ve}", ""),
    "poet": ("{poem}-{ve}", ""), "actor": ("{perform}-{ve}", "LA actor < agere"),
    "leader": ("{lead}-{ve}", ""), "rebel": ("{rebellion}-{ve}", ""), "prisoner": ("{prison}-{ve}", ""),
    "refugee": ("{escape}-{ve}", ""), "diplomat": ("{treaty}-{ve}", ""),
    "envoy": ("{send}+{participle-ik}-{ve}", "the sent one: LA missus, legatus"),
    "representative": ("{represent}-{ve}", ""), "official": ("{office}-{ve}", ""),
    "record-keeper": ("{record}-{ve}", ""), "border-guard": ("{border}-{guard}", ""),
    "healer": ("{vo}-{ve}", "canon vo 'heal' + ve: JA i-sha"),
    "judge": ("{law}-{ve}", "law one: LA iu-dex 'law-speaker'"),
    "visitor": ("{visit}-{ve}", "canon tozhi 'visit'"), "servant": ("{serve}-{ve}", ""),
    "neighbor": ("{near}-{ve}", "EN neigh-bour 'near-dweller', JA rin-jin"),
    "citizen": ("{city}-{ve}", "EN citizen < city, JA shi-min"),
    "individual": ("{one}-{person}", "one person: canon banut"),
    "bondmate": ("{koon}-{ve}", "canon koon 'bond' + ve"),
    "matriarch": ("{clan}-{mother}", "clan-mother"),
    # ---------- places ----------
    "kitchen": ("{cook}+{place-suf}", "LA coquina < coquere, JA dai-dokoro"),
    "library": ("{scroll}+{place-suf}", "JA to-sho-kan 'book house'"),
    "school": ("{learn}+{place-suf}", "JA gak-kou 'learning building'"),
    "laboratory": ("{experiment}+{place-suf}", "LA laboratorium"),
    "temple": ("{deity}+{place-suf}", "JA jin-ja 'god shrine'"),
    "market": ("{trade}+{place-suf}", "LA mercatus, JA ichi-ba 'market place'"),
    "spaceport": ("{void}-{ship}+{place-suf}", "JA kuu-kou"),
    "embassy": ("{ambassador}+{place-suf}", "JA tai-shi-kan"),
    "archive": ("{record}+{place-suf}", "LA archivum"),
    "theater": ("{perform}+{place-suf}", "JA geki-jou"),
    "bath": ("{wash}+{place-suf}", "LA balneum, JA fu-ro-ba"),
    "ship-bridge": ("{command-v}+{place-suf}", "the command place"),
    "capital": ("{head}-{city}", "LA caput 'head', JA shu-to 'head city'"),
    "wind-shelter": ("{wind}-{shield}", ""), "shade-tree": ("{shade}-{tree}", ""),
    "desert-bloom": ("{desert}-{flower}", ""), "carrion-bird": ("{dead}-{bird}", "canon sivusi 'dead'"),
    "pack-beast": ("{carry}-{beast}", ""), "burrower": ("{dig}-{beast}", ""),
    "root-crop": ("{root}-{food}", ""), "salt-flat": ("{salt}-{plain}", ""),
    "thornbush": ("{thorn}-{tree}", ""), "heatwave": ("{heat}-{wave}", ""),
    "mirage": ("{false}-{water}", "culture: the desert's false water"),
    "east": ("{sun}-{rise}", "LA oriens 'rising'"), "west": ("{sun}-{fall}", "LA occidens 'falling'"),
    "orbit": ("{around}-{path}", "JA ki-dou"),
    "shuttle": ("{small}-{ship}", "small ship: JA kogata-tei"),
    "subspace": ("{under}-{void}", "EN sub-space"),
    "asteroid": ("{small}-{world}", "JA shou-wakusei 'small planet'"),
    "antimatter": ("{opposite}-{matter}", "EN anti-matter, JA han-busshitsu"),
    "atom": ("{without}-{cut}", "Greek a-tomos 'uncuttable'"),
    "particle-n": ("{small}-{thing}", "JA ryuu-shi"),
    "temperature": ("{heat}-{degree}", "JA on-do 'warmth degree'"),
    "pressure": ("{push}-{force}", "JA atsu-ryoku 'press force'"),
    "federation": ("{world}-{kau}", "worlds joined, on the canon pattern kash-kau 'minds joined'"),
    "fleet": ("{ship}+{collective}", "JA kan-tai 'ship band'"),
    "audience": ("{hear}+{collective}", "LA audientia < audire"),
    "assembly": ("{meet}+{collective}", ""),
    "clan-war": ("{clan}-{war}", ""),
    # ---------- instruments ----------
    "telescope": ("{distant}-{see}+{instrument}", "Greek tele-skopos 'far-seeing', JA bou-en-kyou"),
    "microscope": ("{small}-{see}+{instrument}", "JA ken-bi-kyou"),
    "sensor": ("{feel}+{instrument}", "LA sensorium"),
    "communicator": ("{communicate}+{instrument}", ""),
    "transporter": ("{carry}+{instrument}", ""),
    "computer": ("{calculate}+{instrument}", "JA kei-san-ki 'calculating machine'"),
    "mirror": ("{see}+{instrument}", "LA speculum < specere 'look'"),
    "lamp": ("{light}+{instrument}", ""),
    "alarm": ("{warn}+{instrument}", ""),
    "instrument-m": ("{music}+{instrument}", "JA gak-ki"),
    "firepot": ("{far}-{pot}", "canon far 'fire' + pot"),
    "fuel": ("{burn}-{thing}", "JA nen-ryou 'burning material'"),
    "game-piece": ("{game}-{stone}", "as Go stones"),
    # ---------- verbs: -tor "make, do" (canon dif-tor), kau "together", and prefixes ----------
    "cooperate": ("{work}-{kau}", "work joined: LA co-operari, JA kyou-ryoku suru"),
    "unite": ("{kau}-{tor}", "make joined: LA unire"),
    "free-v": ("{free}-{tor}", "make free: LA liberare"),
    "respect-v": ("{respect}-{tor}", "JA son-kei suru"),
    "doubt-v": ("{doubt}-{tor}", "JA utagau"),
    "explain": ("{clear}-{tor}", "make clear: LA ex-planare 'make plain', JA setsu-mei 'explain bright'"),
    "define": ("{end}-{tor}", "set the end: LA de-finire"),
    "verify": ("{true}-{tor}", "make true: LA veri-ficare"),
    "repair": ("{whole}-{tor}", "make whole"),
    "improve": ("{good}-{tor}", "make good: JA kai-zen"),
    "prepare": ("{before}-{tor}", "do before: LA prae-parare"),
    "arrange": ("{order}-{tor}", "make order"),
    "clean-v": ("{clean}-{tor}", ""),
    "partition": ("{part}-{tor}", ""),
    "transform": ("{other}-{tor}", "make other: JA hen-kei"),
    "return": ("{again}-{come}", "again + come: LA re-venire"),
    "restore": ("{again}-{build}", "build again: LA re-staurare"),
    "recognize": ("{again}-{know}", "know again: LA re-cognoscere"),
    "reconcile": ("{again}-{kau}", "joined again: LA re-conciliare"),
    "predict": ("{before}-{say}", "say before: LA prae-dicere, JA yo-gen"),
    "translate": ("{across}-{carry}", "carry across: LA trans-latus"),
    "include": ("{in}-{take}", "LA in-cludere"),
    "exclude": ("{outside}-{put}", "LA ex-cludere"),
    "contain": ("{in}-{hold}", "LA con-tinere"),
    "depend": ("{from}-{hang}", "hang from: LA de-pendere"),
    "approach": ("{near}-{come}", "LA ap-propiare"),
    "express": ("{outside}-{push}", "press out: LA ex-primere"),
    "invade": ("{in}-{attack}", "LA in-vadere"),
    "elect": ("{vote}-{choose}", "LA e-ligere 'choose out'"),
    "activate": ("{energy}-{kar}", "canon kar 'kindle, set going'"),
    "swear-fealty": ("{loyal}-{swear}", ""),
    # ---------- learning: canon pattern mik t'X, "inquiry of X" ----------
    "mathematics": ("{inquiry} t'+{number}", "inquiry of number: JA suu-gaku"),
    "astronomy": ("{inquiry} t'+{star}", "inquiry of stars: JA ten-mon-gaku"),
    "biology": ("{inquiry} t'+{life}", "inquiry of life: JA sei-butsu-gaku"),
    "chemistry": ("{inquiry} t'+{element}", "inquiry of elements"),
    "physics": ("{inquiry} t'+{matter}", "inquiry of matter: JA butsu-ri-gaku"),
    "history": ("{inquiry} t'+{past}", "inquiry of the past"),
    "calligraphy": ("{write}-{way}", "the way of writing: JA sho-dou"),
    # ---------- other compounds ----------
    "vegetable": ("{plant}-{food}", "canon glomak: JA ya-sai"),
    "flour": ("{grain}-{dust}", "grain dust"),
    "gift": ("{give}-{thing}", "JA oku-ri-mono 'given thing'"),
    "news": ("{new}-{word}", "EN news < new"),
    "message": ("{send}-{word}", "JA den-gon 'conveyed word'"),
    "language": ("{tongue}+{abstract}", "LA lingua 'tongue', EN tongue"),
    "proverb": ("{old}-{word}", "LA pro-verbium"),
    "chronicle": ("{pon}-{record}", "time-record: Greek chronos"),
    "calendar": ("{day}-{record}", ""),
    "century": ("{hundred}-{year}", "JA sei-ki, LA saeculum"),
    "percent": ("{hundred}-{part}", "LA per centum"),
    "maximum": ("{most}-{big}", "LA maximus, the superlative of magnus"),
    "minimum": ("{most}-{small}", "LA minimus"),
    "quarter": ("{four}+{ordinal}", "fourth: LA quartus"),
    "third-part": ("{three}+{ordinal}", "third: LA tertius"),
    "compassion": ("{with}-{suffering}", "suffering with: LA com-passio"),
    "right-naming": ("{correct}-{name}", "JA sei-mei, Confucian zheng ming"),
    "non-attachment": ("{without}-{koon}", "without bond: JA mu-shuujaku"),
    "secret-n": ("{secret}-{thing}", ""),
}


def ERA(e):
    return ERA_RANK.get(e or "Tribal", 0)


def expand(parts, table, seen=()):
    """Replace a {key} that is itself derived by its own parts, so every piece is a root."""
    def sub(m):
        k = m.group(1)
        if k in table and k not in seen:
            inner = expand(table[k][0], table, seen + (k,))
            return inner
        return m.group(0)
    return re.sub(r"\{([^}]+)\}", sub, parts)


def main():
    path = ROOT / "lexicon" / "meanings.csv"
    rows = list(csv.DictReader(open(path, newline="")))
    F = list(rows[0].keys())
    by = {r["key"]: r for r in rows}
    # new affixes
    for key, gloss, pos, era, notes in NEW_AFFIXES:
        if key not in by:
            r = {k: "" for k in F}
            r.update(key=key, gloss=gloss, pos=pos, field="grammar", kind="core", register="everyday", era=era, notes=notes)
            rows.append(r)
            by[key] = r
    # later batches keep their built words in lexicon/derivations.csv (key, gloss, pos, field, era, register, parts, basis);
    # a key not yet in meanings.csv is added from that row
    extra = ROOT / "lexicon" / "derivations.csv"
    if extra.exists():
        for d in csv.DictReader(open(extra, newline="")):
            if d["key"] not in by:
                r = {k: "" for k in F}
                r.update(key=d["key"], gloss=d["gloss"], pos=d["pos"], field=d["field"], kind="core",
                         register=d.get("register") or "everyday", era=d["era"])
                rows.append(r)
                by[d["key"]] = r
            D[d["key"]] = (d["parts"], d["basis"])
    # retire what the new system replaces: the generated agent suffix (canon ve does the job) and learner (= student)
    rows = [r for r in rows if r["key"] not in ("agent", "learner")]
    by = {r["key"]: r for r in rows}
    # every compound, old or new, is expanded down to roots (a compound has no root form of its own)
    table = {r["key"]: (r["parts"], "") for r in rows if r["kind"] == "compound" and r["parts"]}
    table.update(D)
    for r in rows:
        if r["kind"] == "compound" and r["key"] not in D and r["parts"]:
            r["parts"] = expand(r["parts"], table)
    missing, raised = [], []
    for key, (parts, basis) in D.items():
        if key not in by:
            missing.append(key)
            continue
        r = by[key]
        if r["kind"] in ("anchor", "aligned", "design"):
            missing.append(key + " (canon or designed: not rebuilt)")
            continue
        full = expand(parts, table)
        for k in re.findall(r"\{([^}]+)\}", full):
            if k not in by:
                missing.append(f"{key}: part {k}")
        part_eras = [ERA(by[k]["era"]) for k in re.findall(r"\{([^}]+)\}", full) if k in by]
        need = max(part_eras + [0])
        if ERA(r["era"]) < need:
            new_era = [e for e, n in ERA_RANK.items() if n == need][0]
            raised.append(f"{key}: {r['era']} > {new_era}")
            r["era"] = new_era
        r.update(kind="compound", parts=full, proto="")
        r["notes"] = ("Built: " + basis) if basis else "Built from older words"
    w = csv.DictWriter(open(path, "w", newline=""), fieldnames=F)
    w.writeheader()
    w.writerows(rows)
    print(f"{len(D)} built meanings; {len(rows)} meanings in all")
    if missing:
        print("PROBLEMS:", "; ".join(missing))
    if raised:
        print(f"{len(raised)} eras raised to match their parts:", "; ".join(raised))


if __name__ == "__main__":
    main()
