# MENTIONS LÉGALES ET ATTRIBUTIONS DES RESSOURCES TIERCES
# OBSIDIA BRODY CONVERGENCE V1

Date de publication : 2026-11-18  
Statut des données : LEXICON_PUBLICATION_HOLD (Compilation locale chez l'utilisateur)

---

## 1. Principe Général et Gouvernance des Données

Le projet Brody utilise pour son analyse linguistique des ressources lexicales, morphologiques et sémantiques ouvertes issues de la recherche linguistique publique.

Conformément à la politique d'audit `LEXICON_PUBLICATION_HOLD`, aucune base lexicale binaire compilée (`lexicon.db`) n'est distribuée dans ce dépôt ni sur les plateformes de téléchargement. Le présent dépôt fournit exclusivement des scripts d'ingestion reproductibles (`scripts/download_linguistic_corpora.py` et `scripts/build_linguistic_corpus.py`) permettant à chaque utilisateur d'acquérir et de compiler localement ces ressources pour son usage privé.

---

## 2. Inventaire Détaillé des 8 Corpus et Attributions Officielles

Les 8 jeux de données tiers exploités par la chaîne d'outillage de Brody sont les suivants :

### 1. Morphalou 3.1
* **Identifiant :** `morphalou_3_1`
* **Langue :** Français
* **Licence :** LGPL-LR (Lesser General Public License For Linguistic Resources)
* **Attribution / Ayant-droit :** ATILF CNRS / ORTOLANG (Marie Tonnelier, ANR-11-EQPX-0032)
* **Source amont :** https://www.ortolang.fr/market/lexicons/morphalou/v3.1
* **Empreinte SHA256 :** `4fc815cbf17aecdf1b47f6bbc263489a460fd8d11ae17e6b522336c72bd0e333`
* **Rôle :** Lexique morphologique exhaustif des verbes, noms, adjectifs et adverbes français ; tables de conjugaison complètes.

### 2. UniMorph French
* **Identifiant :** `unimorph_fra`
* **Langue :** Français
* **Licence :** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
* **Attribution / Ayant-droit :** UniMorph Consortium (Universal Morphological Ant)
* **Source amont :** https://github.com/unimorph/fra
* **Empreinte SHA256 :** `4760fc36435a9ffba9b4de6f0787d8eca5b15022e6b141e3b242b129f0d88dcb`
* **Rôle :** Paradigmes morphologiques et flexions verbales françaises.

### 3. UniMorph English
* **Identifiant :** `unimorph_eng`
* **Langue :** Anglais
* **Licence :** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
* **Attribution / Ayant-droit :** UniMorph Consortium (Universal Morphological Ant)
* **Source amont :** https://github.com/unimorph/eng
* **Empreinte SHA256 :** `20a191cefdc7cad6fa74b00f49d6f658684f17b14541aae372e5a3d5a8c15c67`
* **Rôle :** Paradigmes morphologiques standardisés des verbes réguliers et irréguliers anglais, pluriels nominaux et adjectifs.

### 4. Princeton WordNet Morphological Exceptions
* **Identifiant :** `wordnet_exc`
* **Langue :** Anglais
* **Licence :** WordNet 3.0 License (BSD-style)
* **Attribution / Ayant-droit :** Princeton University / NLTK
* **Source amont :** https://github.com/nltk/nltk_data
* **Empreinte SHA256 :** `cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59`
* **Rôle :** Exceptions morphologiques irrégulières pour les verbes, noms, adjectifs et adverbes anglais.

### 5. Open English WordNet 2025
* **Identifiant :** `oewn_2025`
* **Langue :** Anglais
* **Licence :** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Attribution / Ayant-droit :** Global WordNet Association / Princeton University WordNet
* **Source amont :** https://github.com/globalwordnet/english-wordnet/releases/tag/2025-edition
* **Empreinte SHA256 :** `7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`
* **Rôle :** Réseau sémantique lexical anglais fournissant définitions, synsets, synonymes, antonymes et relations de sens.

### 6. French Thesaurus (Dicollecte / LibreOffice)
* **Identifiant :** `thes_fr`
* **Langue :** Français
* **Licence :** Triple licence MPL 2.0 / LGPL 3.0 / GPL 3.0
* **Attribution / Ayant-droit :** Dicollecte (Olivier R.) / LibreOffice Dictionaries
* **Source amont :** https://github.com/LibreOffice/dictionaries/tree/master/fr_FR
* **Empreinte SHA256 :** `52efa736c37f98d7f0abfe5dd4345b6f712880ca0ca664c15a8168d9475a0b46`
* **Rôle :** Synonymes et groupes sémantiques français pour verbes, noms, adjectifs et adverbes.

### 7. XMLittré (Dictionnaire de la langue française par Émile Littré)
* **Identifiant :** `xmlittre_fr`
* **Langue :** Français
* **Licence :** Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0) / Domaine Public
* **Attribution / Ayant-droit :** François Gannaz / Émile Littré (www.littre.org)
* **Source amont :** https://bitbucket.org/Mytskine/xmlittre-data
* **Empreinte SHA256 :** `7d2f4205b70b49d0d6503cb0f9b70b16ee428350be8f8c3260ad1d5876274448`
* **Rôle :** Dictionnaire historique et général de référence pour les définitions et catégories grammaticales françaises.

### 8. FreeDict French-English Dictionary
* **Identifiant :** `freedict_fra_eng`
* **Langue :** Français - Anglais
* **Licence :** GNU General Public License v2 or later (GPL v2+)
* **Attribution / Ayant-droit :** FreeDict Project (Vincent Ramos / Horst Eyermann)
* **Source amont :** https://github.com/freedict/fd-dictionaries
* **Empreinte SHA256 :** `de9eb6e5756d994bca9bdb2a91bfc2bb8d8822d3387f5a3b586acc8d42133114`
* **Rôle :** Gloses de traduction bilingue français-anglais et correspondances lexicales.

---

## 3. Déclaration Contractuelle sur la Licence du Dépôt

Le code source d'orchestration, les résolveurs et les scripts présents dans ce dépôt sont indépendants des données linguistiques brutes.  
Les métadonnées factuelles (URLs, empreintes SHA256) déclarées dans `data/linguistic_corpus/DOWNLOAD_MANIFEST.json` constituent des informations d'interopérabilité technique et ne confèrent aucun droit de propriété sur les contenus des ayants-droit cités ci-dessus.
