# Audit: the dictionary against canon, the novels, the VLD and fandom

Run 18 Nov 2026 against the project dictionary at batch 23 (3,440 entries). Sources checked:
- `corpus/canon.csv`: 114 on-screen items.
- `corpus/novel.csv`: 42 novel and RPG items.
- The best-known VLD (Vulcan Language Dictionary, Vulcan Language Institute) and fanfiction words, as quoted in public fan glossaries.

The full VLD could not be checked: its site and the copies of it on Google Drive are blocked in this workspace (see section 5).

## 1. Summary

| Check | Result |
|---|---|
| On-screen and novel words present in the dictionary | All but 4 glossed words (section 3) |
| Glosses that contradict canon | None found. One conflict is already logged: Decipher's *koon* "challenge" was rejected in favour of canon *koon* "bond" |
| Canon words stored under a respelling | **27**, and only 3 of them use the exception mechanism (*sehlat*, *kal-toh*, *pon farr*) |
| Notes that contradict the stored form | 1 (*qui'lari*) |
| Our words that clash with a famous VLD or fandom word | None exact. Three near-misses (section 4) |
| Famous fandom words with no entry at all | 15 of the 16 checked (only *ozh'esta* is in) |

## 2. Spelling: canon words respelled to the house orthography

The house rule ("one consistent spelling that adapts canon") respells source words. It drops a vowel-lengthening *h*, writes *c* and *q* as *k*, and removes hyphens. As a result, a writer who looks up a famous word finds a spelling that is not the one on screen. The rule is also applied unevenly: *sehlat*, *kal-toh* and *pon farr* keep their canon spelling through a logged exception, but the 27 words below do not.

**On screen (TV and film):**

| Screen spelling | Dictionary now | Source |
|---|---|---|
| kroykah | kroika | TOS "Amok Time" |
| ahn-woon | anwoon | TOS "Amok Time" |
| kal-if-fee | kalifee (in koon-ut-kalifee) | TOS "Amok Time" |
| kahs-wan | kaswan | TAS "Yesteryear" |
| Kolinahr | kolinar | Star Trek: TMP |
| Nahp | nap | Star Trek: TMP |
| eh ("and") | e | Star Trek: TMP |
| ish-veh, nash-veh | ish-ve, nash-ve (and every *-ve* noun: 330 entries) | Star Trek II |
| ot-lan | otlan | Star Trek II |
| Ghishun | gishun | ENT "Home" |
| k'oh-nar | k'onar | VOY "Alter Ego" |
| soo-lak | soolak | VOY "Alter Ego" |
| shon-ha'lock | shon-ha'lok | VOY "Gravity" |
| qui'lari | kui'lari (Ceremonial keeps qui'lari) | DS9 "The Muse" |
| suus mahna | suus mana | ENT "Marauders" |
| surah'tahn | sura'tan | ENT "Rajiin" |
| mol-kom | molkom | ENT "Shuttlepod One" |
| tarul-etek | taruletek | ENT "Horizon" |
| pahk | pak | ENT "Fallen Hero" |

**Novels and RPG:** cthia → kthia, kah → ka, kah-if-fee → kahifee, klee-fah → kleefa, loshiraq → loshirak, ashv'cezh → ashv'kezh, Av'adeh'dna → av'ade'dna, yeht → yet, pahn-ree → panree, and the sentence forms *Mene sakkhet ur-seveh* and *terau-kashkau-veh-shetau*.

**Contradiction to fix:** the note on *qui'lari* says it "keeps old q because medical terms froze in Classical form", but its Standard form is *kui'lari*. Either the note or the form is wrong.

**Pronunciation is not the problem:** `docs/pronunciation.md` already teaches *nash-ve* as NASH-veh. The two diverge only in writing.

## 3. Canon and novel words with no usable entry

| Word | Gloss | Source | Note |
|---|---|---|---|
| fal-tor-voh | meld treatment for a neurodegenerative disease | VOY "Endgame" | The dictionary has *fal-tor-vo*; the screen spelling has *h* |
| yeht | true | Decipher RPG | Entered as *yet*, which collides with the English word *yet*. Our *patu* also means "true" |
| fal chaya | noble endeavour | Decipher RPG | Its parts *fal* and *chaya* exist; the phrase itself has no entry |
| tor-ut koon | sacred challenge | Decipher RPG | Rejected in batch 2 because canon *koon* means "bond". Keep it rejected |

Untranslated canon sentences (*Ishtaya kulah*, *Shanshot tulara komosh*, *Tiar merra*) and Duane's untranslated Old Vulcan lines stay in the corpus only. That is correct.

**Not yet checked:** the newer series (DIS seasons 3–5, PIC, LD, PRO, SNW seasons 1–3). The corpus has the DIS lines and *The Sehlat Who Ate Its Tail* (SNW), but the newer series have not had a transcript pass.

## 4. The VLD and fandom

What the VLD is: Mark R. Gardner's Golic Vulcan, published by the Vulcan Language Institute. It is the largest fan Vulcan, at roughly 7,000+ words in the Memrise mirror. Its grammar puts the verb first. It is **not canon**, and it does not mark which of its words are canon and which are fanon.

### Famous fandom words, checked against this dictionary

| Fandom word | Meaning | Origin | Here now |
|---|---|---|---|
| ashaya / ashau | love (noun / verb) | VLD | *shlel* love |
| ashayam | beloved; the VLD notes it is used "mainly in fanfiction" | VLD | *shlelik* beloved |
| ashal-veh, ashalik | darling | VLD | no entry |
| taluhk | precious, dear | VLD | no entry |
| tal-kam | dear | VLD | no entry |
| k'diwa | beloved | Jean Lorrah, *NTM* novels | no entry |
| adun / adun'a | husband / wife | Jean Lorrah | *koon-ve* bondmate |
| shok-tor | kiss | VLD | *teya-nakan* (the Human kiss) |
| nartau, teraya-martaya | embrace, hug | VLD | *khefil-kire* hug |
| el'ru'esta | hand-embrace, hold hands | VLD | *poth-kire* hold hands |
| ozh'esta | finger embrace | VLD | **adopted** in batch 6 as the old or colloquial word |
| lok | penis | VLD | *keknil* (vulgar), *kanuh-khasni* (clinical) |
| sa-mekh | father | VLD | *lausan* |
| tonk'peh | hello | VLI lessons | no entry (*t'nar* is the canon greeting) |
| nam-tor | to be | VLI lessons | *wim* (canon, aligned from *wimish*) |
| du | you | VLI lessons | *tu* (canon) |

**Near-misses** that a fandom reader might misread:
- our *lokh* "sea" against VLD *lok* "penis"
- our *uhf-* "without" against VLD *uf* "how"
- our *haru* "tribute" against VLD *aru* "evening"

None is an exact clash. *Lokh* is the only one worth watching in prose.

**Already established precedent:** batch 6 took *ozh'esta* from fandom as an older or colloquial word beside the Surakian *sileil*. Any fandom word can enter the same way, as a dated or register variant, without displacing the canon-built word.

## 5. What a full VLD pass needs

The VLD site (starbase-10.de/vld) and the Google Drive copies of its Vulcan–English and English–Vulcan lists are blocked from this workspace. To check every VLD word, attach either the VLD's own export or those two compiled lists. The audit script then compares all of them automatically: same meaning with a different form, same form with a different meaning, and near-misses.

## 6. Decisions (18 Nov 2026) and what was done

1. **On-screen words keep their screen spelling** (option 1). 26 words became logged exceptions, and every compound follows them. Novel and RPG words keep the house spelling.
2. **The person word is *-veh*.** That changed 328 forms; *nash-veh*, *ish-veh* and *ihk-veh* are now built from their parts.
3. **VLD and fandom words become variants.** 17 were added with an era and register, and none replaces an existing word.
4. **Full VLD pass:** waits on the full VLD lists. The VLD function words (nam-tor, du, ra, uf, rom, aru, lesek, osu, k', and the ko-mekh family) wait for that pass.

Result: 3,457 entries, 0 errors. No id changed, and no Romulan or Ceremonial form changed. 371 Standard forms changed; every one is listed in `analysis/respelled.csv`. Details are in `lexicon/changelog.md`, under "Audit 1".
