# BRODY — OBSIDIA

## Une intelligence à construire autrement

**Conception originale : Etienne Aubin — depuis février 2025**  
**Projet :** [Brody, nouveau genre d'intelligence — dépôt de convergence](https://github.com/Eaubin08/obsidia-brody-LLm--nouveau-genre-convergence-)

> **Et si, pour fabriquer une intelligence, il ne fallait pas commencer par entraîner un modèle à produire des réponses, mais construire ce qui lui permet de recevoir le réel, d'en organiser les relations, d'en conserver le sens, de raisonner, d'apprendre et de s'exprimer ?**

Cette question porte le projet **Brody**. Son origine est plus vaste que le développement d'un chatbot, et sa destination est plus vaste qu'un grand modèle de langage. Brody est le nom donné à l'intelligence conversationnelle native que je cherche à faire émerger dans l'architecture **Obsidia**. Il doit pouvoir utiliser des mots, mais son fonctionnement ne doit pas être prisonnier des mots. Il doit pouvoir répondre, mais sa fonction ne se réduit pas à produire des phrases. Il doit pouvoir acquérir des connaissances sans que chaque apprentissage exige de réentraîner un réseau neuronal.

**À ce stade, le cœur natif de Brody ne repose sur aucun modèle neuronal préalablement entraîné.** Son point de départ est une construction logicielle : règles, représentations, correspondances, structures de sens, traitement des états, calcul, mémoire et interfaces entre des fonctions spécialisées. Des outils neuronaux existants peuvent être employés à la périphérie, comme auxiliaires, sans constituer ce cœur. Cette frontière est une caractéristique de la conception, non une négation de l'utilité des autres approches.

Ce dépôt a une fonction concrète : **réunir les capacités Brody déjà développées dans les différentes parties d'Obsidia pour rendre cette conception exécutable, compréhensible et vérifiable**. Ce README raconte d'abord *ce que l'on construit et pourquoi* ; l'inventaire des fichiers et des travaux d'intégration vient seulement ensuite.

---

## Le point de départ : construire avec ce que je ne savais pas

Je ne suis pas parti d'un laboratoire possédant toutes les connaissances, toutes les machines et un plan de recherche déjà défini. Je suis parti d'interrogations.

J'avais devant moi des systèmes capables de parler, d'écrire du code, de calculer, d'aller chercher des documents, de simuler du raisonnement et de commander des outils. Pourtant, une réponse convaincante ne garantissait ni la vérité, ni la mémoire, ni la compréhension de ce qui avait été demandé. Un moteur pouvait accomplir une tâche sans savoir ce qu'un autre moteur avait déjà résolu. Une IA pouvait sembler apprendre au cours d'une conversation et tout perdre en changeant de contexte. Elle pouvait aussi présenter une hypothèse comme une certitude.

Je n'avais pas toutes les compétences techniques au départ. **J'ai donc commencé par poser les questions que je ne savais pas encore poser correctement.** Une question appelait un essai ; un essai révélait un trou ; ce trou obligeait à modifier l'architecture. C'est dans cette succession de questions qu'est né Obsidia.

L'une des plus importantes fut : **qu'est-ce que « comprendre » veut dire pour une machine, si la machine ne parle pas le langage dans lequel je lui explique le monde ?**

Une autre suivait immédiatement : **pourquoi faudrait-il entraîner une machine sur toutes les réponses possibles alors que le monde est structuré, que les règles existent, que des connaissances peuvent être reliées et que les compétences peuvent être accueillies au fur et à mesure ?**

Puis une troisième : **comment empêcher les erreurs et les contradictions de traverser tout le système en se transformant progressivement en vérités ou en autorisations ?**

Les réponses n'ont pas été des slogans. Elles ont orienté la construction de couches logicielles, de moteurs, de contrats, de contrôles et de mémoires. Elles ont aussi conduit à des impasses, à des révisions et à des versions concurrentes. Le projet ne cache pas cette histoire : **la correction des erreurs fait partie de sa méthode de création**.

Je n'ai pas recréé tous les chemins de l'informatique, des mathématiques, de la linguistique ou de la robotique. J'ai progressivement compris qu'il fallait **préparer l'espace dans lequel ces chemins pourraient se rejoindre**. C'est le principe *ex ante* qui a donné sa cohérence à Obsidia.

---

## 1 — Ce qu'est Brody, et ce qu'il n'est pas

L'expression « pseudo-LLM » ou « LLM d'un nouveau genre » permet de désigner publiquement un système qui doit dialoguer avec l'humain. Mais elle peut aussi induire en erreur si l'on imagine un transformeur classique simplement plus petit, quantifié ou spécialisé.

**Le projet n'est pas de faire un LLM moins cher.** Il est de rechercher une autre organisation de l'intelligence :

- recevoir des informations exprimées dans des langages différents ;
- déterminer ce qu'elles désignent et ce qui les relie ;
- organiser des représentations indépendantes de la formulation exacte des mots ;
- conserver les faits, les expériences, les contradictions et les inconnus ;
- trouver une solution par des règles, des relations, des outils et des déductions ;
- apprendre et évoluer en ajoutant ou en révisant des structures, non en réentraînant systématiquement un modèle ;
- reformuler enfin le résultat dans la langue et à la hauteur de compréhension de l'interlocuteur ;
- rester sous une gouvernance explicite lorsqu'une proposition pourrait devenir une action.

Brody n'a pas à contenir toute la puissance de l'écosystème dans son propre moteur. **Il doit savoir interpréter ce qui arrive, faire travailler ce qui existe, maintenir la cohérence du parcours et restituer le résultat.** Il est ainsi l'organe de compréhension et de dialogue d'un ensemble plus large.

Une connaissance peut exister sans qu'elle soit écrite dans les poids d'un réseau neuronal. Une règle de conjugaison peut être une règle exécutable. Une relation causale peut être représentée comme un lien typé. Un calcul peut être confié à un solveur exact. Un événement peut être enregistré avec sa date et sa provenance. Une compétence spécialisée peut répondre à un contrat. Un résultat peut être vérifié avant d'être restitué.

La recherche vise à découvrir **jusqu'où cette composition peut aller**, et dans quels cas elle rencontre ses limites. Le fait que la voie soit différente ne dispense pas de prouver la qualité de ses réponses. Mais la question expérimentale devient différente : *quelles formes de compréhension et d'apprentissage peut-on construire à partir de structures et de relations, sans entraîner au préalable un modèle neuronal qui imiterait toutes ces fonctions ?*

---

## 2 — La clé : chacun parle son langage

Ce qui a rendu cette conception possible est une idée simple, mais profonde : **chaque couche d'une machine, chaque domaine et chaque interlocuteur possède son langage propre.**

Pour nous, une phrase est une manière de communiquer une intention. Pour un processeur, elle n'est qu'une succession de données encodées qui finissent en opérations et en états. Pour une base relationnelle, le monde apparaît sous forme d'enregistrements et de liens. Pour un moteur logique, une proposition existe avec ses prémisses, ses règles de transformation et ses conditions de validité. Pour un capteur, il existe des signaux. Pour une mémoire, il existe des traces et des relations dans le temps.

**Aucune de ces couches n'a besoin de devenir l'autre pour communiquer avec elle.** Elles ont besoin d'un passage qui conserve les informations utiles et sache exprimer ce qui n'est pas transposable.

### Remonter du binaire jusqu'au sens

Prenons le trajet inverse d'une réponse humaine :

1. Une réponse affichée est une suite de mots.
2. Ces mots représentent des relations, des objets, des actions, des hypothèses et une intention.
3. Ces relations peuvent être décrites par des structures intermédiaires.
4. Ces structures peuvent être traitées par des programmes, des règles et des graphes.
5. Ces programmes reposent finalement sur des opérations et des états binaires.

Il ne s'agit pas de prétendre que le binaire « comprend » les mots. Il s'agit de définir **les correspondances qui permettent à un niveau de fournir à l'autre ce dont il a besoin, sans lui attribuer un pouvoir qu'il ne possède pas**.

Le problème peut donc être posé dans les deux sens : comment passer d'une expression humaine à des structures exploitables par la machine ? Et comment revenir d'une opération machine à une explication humaine sans inventer de sens pendant le trajet ?

### Les cinq couches de référence

| Couche | Nom dans la conception | Son univers d'expression | Sa mission |
|---|---|---|---|
| **OS0** | Moteur | États, binaire, opérations, transitions | Exécuter les opérations matérielles et logicielles admissibles |
| **OS1** | Cognitif / Cortex | Structures, règles, graphes, représentations intermédiaires | Construire et exploiter les relations utiles |
| **OS2** | MCP / intégration | Contrats, appels, formats, outils, domaines | Faire coopérer les capacités spécialisées |
| **OS3** | Reverse OS | Reconstruction de la signification vers l'interlocuteur | Expliquer les résultats sans changer leur statut |
| **OS4** | OS Trad | Traduction et transduction entre représentations | Transporter le sens et les informations d'une couche à l'autre |

Ces cinq plans désignent des **responsabilités architecturales**. Leur numérotation est une cartographie, pas la promesse que toute demande suit toujours cinq étapes linéaires ou que tous les mécanismes historiques sont déjà raccordés dans un même runtime.

### Un exemple : « La porte s'est ouverte parce que quelqu'un est entré »

Dans une conversation, la phrase contient au moins deux événements et une relation causale exprimée par « parce que ». Brody ne doit pas se limiter à mémoriser une chaîne de mots. Il doit pouvoir identifier :

- un événement d'ouverture ;
- un événement d'entrée ;
- des acteurs ou objets qui restent à identifier ;
- un lien causal **affirmé dans la phrase** ;
- le statut de ce lien : est-ce le récit de quelqu'un, une observation ou un fait vérifié ?

La représentation doit conserver cette différence. Si la causalité n'est que déclarée par un utilisateur, elle ne peut pas devenir une loi du monde sans contrôle. Si une observation contredit le récit, la contradiction doit rester visible. Si l'on demande ensuite « pourquoi la porte s'est-elle ouverte ? », Brody doit retrouver la **relation** et sa provenance, pas seulement rechercher des mots similaires.

C'est ainsi que la traduction devient un élément d'intelligence : elle fournit une structure sur laquelle mémoire et raisonnement peuvent réellement travailler.

---

## 3 — OS Trad, OS Trad Uni, Reverse OS et les IR : le système circulatoire du sens

**OS Trad** doit permettre le passage entre représentations. Sa fonction fondamentale n'est ni de prédire des tokens, ni de deviner ce qui n'est pas connu, ni de prendre une décision. Il établit des correspondances explicites : types, fonctions, relations, événements, temps, conditions, états.

**OS Trad Uni** étend le problème à différentes modalités. Une phrase écrite, un son, un message d'outil ou un événement de capteur doivent pouvoir contribuer à une même opération cognitive sans être confondus avec des observations de même nature.

**Reverse OS** réalise la remontée intelligible vers l'humain ou vers un autre interlocuteur. Quand le système dispose d'un résultat logique, d'une valeur numérique, d'une incertitude ou d'un refus, il doit pouvoir l'exposer dans la langue appropriée en conservant sa signification.

Entre eux intervient l'**IR — représentation intermédiaire**. Elle n'a pas pour but d'être une langue universelle miraculeuse. Elle constitue un ensemble de structures et de contrats exploitables par les organes concernés.

L'alphabet de travail historique comporte douze primitives :

`VALUE`, `STATE`, `READ`, `WRITE`, `FLOW`, `COND`, `LOOP`, `CALL`, `RETURN`, `EVENT`, `TIME`, `ERROR`.

Ces primitives expriment des formes élémentaires d'opération. Elles ne suffisent pas à elles seules à représenter toutes les nuances de la pensée. Leur rôle est d'offrir un socle de **passage typé** qui peut être enrichi par des ontologies, des graphes, des contextes et des règles de domaine.

### La fidélité avant l'éloquence

Un traducteur qui perd discrètement une négation, une condition, une provenance ou une contradiction ne rend pas le système intelligent : il le rend dangereux. La politique historique `UNKNOWN_OR_REFUSE` répond à ce problème : quand une signification ne peut être conservée avec les informations disponibles, le système doit **qualifier l'inconnu**, demander une précision ou refuser la transformation.

Ce principe traverse le contrat L2.5 et ses obligations O1–O10 : traçabilité, réversibilité, non-mutation, distinction des droits, restitution explicite, statut consultatif des symboles et frontière avec le noyau souverain.

### Le symbolisme et les Hanzi

Dans mes recherches, les **glyphes, Hanzi et représentations symboliques** ont été explorés comme des moyens de condenser et relier des significations. L'enjeu n'est pas de prétendre qu'une langue serait naturellement supérieure ou qu'un caractère contiendrait une vérité magique. L'intérêt se trouve dans la possibilité de manipuler **des structures de sens qui ne sont pas prisonnières de la phrase française ou anglaise d'origine**.

Une représentation compacte peut être une aide à la mémoire, au rapprochement d'idées ou au changement d'échelle. Pour être utile, elle doit conserver un chemin d'explication vers les langues et les preuves d'origine. Un symbole incompris doit rester incompris ; sa beauté graphique ne lui confère aucune autorité.

### Géométries, arbres et invariants

Les travaux historiques autour du **LTO-16D**, des espaces cognitifs **34D**, de l'**Agent Vecteur**, de **VERBATIA** et du **Clavage** explorent d'autres formes de représentation et de surveillance : intention, contexte, distances, trajectoires, divergences, contraintes. Ils participent à la même recherche : sortir d'une compréhension réduite à une suite de mots et disposer de mécanismes explicites pour détecter une perte de cohérence.

Leur statut opérationnel doit rester vérifiable. **Une géométrie ne prouve pas un raisonnement ; une distance ne prouve pas une vérité ; une projection ne vaut pas observation.** Ces mécanismes sont des instruments possibles de l'intelligence, pas une excuse pour abandonner la preuve.

---

## 4 — L'approche ex ante : concevoir l'accueil avant de connaître les invités

Il y a eu une étape déterminante dans ma manière de construire : **je me suis placé ex ante**.

Je n'ai pas essayé de refaire tous les chemins déjà construits par l'humanité. Je ne pouvais pas inventer à nouveau les mathématiques, tous les langages, tous les domaines métier, toutes les bases de connaissance ou tous les outils. J'ai donc cherché **ce qui doit être vrai avant qu'une nouvelle capacité puisse entrer dans le système**.

Pour accueillir un organe, il faut pouvoir répondre :

1. Que reçoit-il exactement ?
2. Quel langage et quelles structures comprend-il ?
3. Que produit-il et sous quel statut ?
4. Qui peut consommer son résultat ?
5. Qu'a-t-il le droit de lire, de proposer, de modifier ou d'exécuter ?
6. Comment sait-on qu'il fonctionne ?
7. Que fait-on s'il ne sait pas répondre ou si ses résultats contredisent un autre organe ?
8. Comment le remplacer ou le faire évoluer sans détruire ce qui marche déjà ?

Une fois ces questions posées, une fonction nouvellement découverte n'exige plus de reconstruire tout l'organisme. Elle peut être évaluée, traduite, raccordée et contrôlée dans le cadre qui l'attend.

**La nouveauté recherchée n'est pas chaque brique prise séparément. C'est l'architecture qui permet à des briques de natures différentes de coopérer sans que leurs langages, leurs vérités et leurs pouvoirs se confondent.**

### La métaphore du moteur

Une voiture possède un moteur, des capteurs, des routes, des instruments, des commandes et un conducteur. Un tableau de bord ne remplace pas un moteur ; une route ne remplace pas une décision de conduire ; une indication de vitesse ne constitue pas une permission de franchir un obstacle.

**Brody est une partie de l'interface cognitive : il comprend la demande et explique ce que l'organisme sait faire.** D'autres organes exécutent les calculs, vérifient les invariants, modélisent des domaines ou proposent une transformation. Le noyau souverain conserve les frontières de décision. L'ensemble n'a de sens que lorsque ces fonctions sont réunies dans un parcours intelligible.

Cette séparation a une autre conséquence : **on peut construire avec peu de moyens**. Une fonction existante est une ressource. La réinventer consomme du temps, de la mémoire, de l'énergie et des preuves. L'accueillir avec un contrat sûr permet de concentrer les ressources sur ce qui manque réellement.

---

## 5 — Comment Brody peut comprendre sans avoir été entraîné sur la réponse

La difficulté n'est pas simplement de reconnaître des mots. C'est de passer de l'expression à la structure, puis de la structure à une opération possible.

Une phrase a une forme grammaticale ; elle exprime une intention ; elle fait référence à des entités ; elle peut supposer un contexte ; elle peut contenir plusieurs interprétations ; elle peut affirmer une relation sans la prouver. Ces dimensions doivent être traitées séparément avant d'être réunies.

### Un parcours de compréhension native

**1. Recevoir.** L'entrée peut être du texte, puis de la voix ou d'autres signaux, chacun portant sa provenance et son contexte.

**2. Découper.** Le moteur linguistique identifie, autant que ses règles le permettent, les mots, lemmes, flexions, fonctions et structures grammaticales.

**3. Relier.** Les termes sont reliés aux concepts disponibles, aux entités, aux événements, aux relations sémantiques, au contexte et aux incertitudes.

**4. Traduire.** La demande est représentée dans une ou plusieurs IR adaptées aux organes sollicités. Une question n'est pas encore une commande et une commande n'est pas encore une permission.

**5. Chercher et raisonner.** Brody utilise les relations et les mémoires pertinentes, puis fait appel aux compétences spécialisées lorsque celles-ci savent mieux calculer, déduire ou vérifier.

**6. Contrôler.** Le système examine la suffisance des informations, les contradictions et les limites de ce qui est établi. L'absence de preuve ne doit pas déclencher une invention.

**7. Expliquer.** Le résultat revient vers l'interlocuteur par les mécanismes de réalisation et de traduction inverse, sans perdre les nuances, la provenance ou le statut de vérité.

Cette description est **le fonctionnement architectural recherché**. Certaines portions possèdent déjà des implémentations et des tests ; d'autres restent à réunir ou à approfondir. Le passage de ces opérations à une compréhension générale de toute demande **reste une question expérimentale**.

### Exemple : une question jamais apprise mot pour mot

« Si un réservoir contient 125 litres, qu'on en retire 45 et qu'on répartit le reste entre huit récipients, combien chaque récipient reçoit-il ? »

Le système n'a pas besoin d'avoir rencontré cette phrase exacte pendant un entraînement neuronal. Il lui faut reconnaître les objets et les opérations, conserver les quantités et leurs unités, traduire les relations mathématiques et appeler un calcul exact : `(125 - 45) / 8 = 10`.

Ce cas illustre le principe, sans prétendre résoudre toute la compréhension naturelle. La difficulté augmente lorsque les termes deviennent implicites, que les pronoms renvoient à plusieurs objets, que l'information manque ou qu'une métaphore change le sens de la phrase. C'est précisément ce que doivent travailler les couches linguistiques, symboliques et mémorielles.

### Comprendre n'est pas réciter

Le critère recherché n'est pas seulement de répondre à « combien ? » avec le bon nombre. C'est de conserver le bon raisonnement si l'on change les valeurs, l'ordre de présentation, la langue, le contexte ou la manière de poser la question. Puis de reconnaître quand les prémisses ne permettent plus de conclure.

**Une intelligence native doit pouvoir réutiliser des structures sur des situations nouvelles, sans dépendre de la mémorisation de la formulation de ces situations.**

---

## 6 — La mémoire : de la trace à l'expérience, puis à la connaissance

Une grande partie de mon projet repose sur une distinction que je refuse de perdre : **une collection de documents, même bien indexés, n'est pas la mémoire cognitive que je cherche à construire**.

Un document conserve un texte. Une mémoire cognitive doit pouvoir conserver une relation qui a été découverte, une expérience qui a été vécue, une hypothèse qui a été invalidée, un détail dont la pertinence change dans le temps ou une connaissance dont le statut a évolué.

Le corpus, les livres, les conversations et les archives peuvent être **des sources**. Ils ne sont pas automatiquement des expériences, des preuves ou des connaissances.

### Les échelles de mémoire

- **Mémoire de travail** : ce qui est actif dans la situation présente.
- **Mémoire épisodique et événementielle** : ce qui est arrivé, à qui, quand et dans quelles circonstances.
- **Mémoire sémantique et relationnelle** : ce qui est relié à quoi, sous quel type de lien et avec quelle provenance.
- **Mémoire procédurielle** : comment reproduire une opération valide.
- **Mémoire des erreurs et contradictions** : ce qui a échoué, ce qui est contesté et pourquoi.
- **Mémoire fractale et dormante** : organisation à plusieurs échelles, activation de branches pertinentes et mise en veille de ce qui ne l'est plus.
- **Consolidation et oubli gouvernés** : ce qui devient stable, est remplacé, devient inaccessible ou doit être supprimé selon une règle explicite.

Le même événement peut avoir plusieurs dimensions : temporelle, causale, symbolique, spatiale, linguistique, émotionnelle ou fonctionnelle selon les données disponibles. Il ne se réduit pas à un paragraphe rappelé par similarité.

### Huit fondations pour la mémoire cognitive visée

**A — Temps.** Séparer l'instant où le système apprend un fait de la date à laquelle le fait s'est produit. Préserver les séquences, corrections et causalités alléguées.

**B — Graphe relationnel natif.** Établir des liens typés — `CAUSE`, `CONSEQUENCE`, `PART_OF`, `DEPENDS_ON`, `CONTRADICTS`, `SUPPORTS`, `SIMILAR_TO`, `PRECEDES`, `SYMBOLIZES`, `DERIVED_FROM` — dont les sources et les statuts sont connus.

**C — Nuages de points multidimensionnels.** Situer des concepts, états et trajectoires dans des espaces de représentation adaptés. La proximité n'y vaut jamais preuve.

**D — Les 34 arbres.** Organiser plusieurs perspectives d'exploration et permettre leurs activations croisées, sans enfermer une chose dans une seule catégorie.

**E — Fourmis et abeilles.** Explorer des chemins par traces locales, coopération et spécialisation. La métaphore des fourmis inspire des mécanismes de stigmergie ; celle des abeilles, la comparaison de pistes par des unités spécialisées. Leur efficacité doit être définie par des algorithmes bornés et mesurée.

**F — ARS / ARD.** Rechercher les routes, relations symboliques et activations dynamiques entre structures, situations et concepts. Les contrats exacts doivent être récupérés dans les sources historiques plutôt que réinventés.

**G — Langages et symboles.** Raccorder les représentations linguistiques, conceptuelles, visuelles et symboliques via OS Trad, Reverse OS et les IR, sans confondre correspondance et identité.

**H — Évolution et oubli.** Distinguer la candidature, la vérification, la contestation, la supplantation, l'inactivité, la réactivation, la révocation et la corruption ; séparer aussi oubli d'activation, sortie de contexte, invalidation, révocation et suppression.

### Le rôle de l'expérience

Pour qu'une expérience fasse évoluer Brody, il faut davantage qu'un enregistrement. Il faut pouvoir décrire **ce qui était attendu, ce qui a été essayé, ce qui s'est produit, avec quelles preuves et ce qui doit changer**. Cette différence permettrait à Brody de corriger un chemin de résolution sans détruire ses autres connaissances.

L'éducation visée consiste à transformer progressivement des observations contrôlées en aptitudes et en connaissances réutilisables. **Aucune observation ne devient vraie du seul fait qu'elle est répétée**. Aucune contradiction ne doit être effacée uniquement pour rendre la mémoire cohérente en apparence.

La clôture d'écriture **4A1** et la gouvernance **KX108** sont ici des protections fondamentales : pouvoir lire, reconnaître, proposer ou restituer une expérience **n'autorise pas automatiquement son inscription durable**. La mémoire cognitive n'est ni une zone libre d'écriture ni une simple base de documents.

---

## 7 — L'intelligence n'est pas un seul organe : pourquoi Obsidia existe

Une architecture qui cherche à tout faire dans un même moteur reproduit le problème qu'elle voulait résoudre : chaque nouvelle fonction augmente la confusion entre compréhension, calcul, mémoire, décision, vérification et action.

**Obsidia est né pour maintenir ces fonctions distinctes et coopérantes.** Brody n'est pas « tout Obsidia dans un chatbot » ; il est l'une des manières par lesquelles l'organisme peut comprendre une demande et y répondre.

| Organe ou programme | Pourquoi il existe | Ce qu'il apporte à la destination finale |
|---|---|---|
| **Brody** | L'humain s'exprime dans une langue ambiguë et changeante | Compréhension, dialogue, coordination cognitive et restitution intelligible |
| **SENS** | Le monde arrive comme des signaux et des observations hétérogènes | Qualification et structuration des entrées |
| **Sigma** | Les règles et les calculs ne doivent pas devenir des approximations rhétoriques | Calcul exact, évaluations et invariants de domaine |
| **Obsidure** | Une intelligence doit pouvoir construire et vérifier des programmes sans mutation aveugle | Développement gouverné, contrats, contrôles et preuves |
| **KX108 / X-108** | Savoir proposer ne donne pas le droit de décider ou d'agir | Autorité souveraine, gardes, `ACT`, `HOLD`, `BLOCK` |
| **Monde / World** | Le réel et ses objets ne sont pas les souvenirs du système | Modèles d'environnement, ontologies et frontières d'action |
| **Native Memory / 4A1** | L'expérience doit persister sans devenir une vérité ou une écriture arbitraire | Continuité, relations, provenance et règles d'écriture |
| **Studio E11** | Une réponse complexe demande de la structure, de la lisibilité et du contrôle de cohérence | Composition longue à partir de matériaux admis |
| **JarJar** | Une intelligence conversationnelle ne doit pas être limitée au clavier | Écoute, dialogue oral, restitution vocale |
| **Oxygen** | Un système figé ne peut pas suivre les expériences et les compétences nouvelles | Éducation, maturation et développement progressif sous règles |

L'enjeu n'est pas de multiplier les agents pour faire une démonstration impressionnante. Il est de permettre **à chaque capacité de parler sa propre langue, d'être utilisée à sa juste place et de rester remplaçable**.

### La constitution de l'organisme

Le principe historique **« capacité n'est pas autorité »** est décisif. Une phrase générée par Brody n'est pas une décision. Un résultat de calcul n'est pas un permis d'agir. Un score de similarité n'est pas une preuve. Un souvenir n'est pas une loi. Une suggestion de moteur externe n'est pas un mandat.

Le noyau **KX108** doit traiter les questions de décision dans le cadre des règles et des preuves admissibles. Le projet explore une sûreté inspirée d'**Asimov distribué** : contrôles, sentinelles et frontières placés dans les flux, non simple filtre final ajouté à une réponse.

Les preuves formelles, notamment dans **Lean 4**, servent à établir des propriétés précises des contrats et des transitions. L'exigence du projet est un contrôle réel des axiomes, de l'absence de `sorry` et des hypothèses, sans conclure qu'un théorème local prouve à lui seul la perfection de tout l'organisme.

**Le système doit rester capable de dire « je ne sais pas », « les sources se contredisent » ou « cette action n'est pas admissible ». Cette retenue fait partie de l'intelligence visée, pas d'une limitation à dissimuler.**

---

## 8 — Une intelligence qui évolue sans réentraînement neuronal systématique

Le principe est central et mérite d'être formulé sans ambiguïté : **Brody est conçu pour démarrer et fonctionner nativement sans entraînement préalable d'un modèle neuronal.** Son socle n'est pas le résultat d'une optimisation de milliards de poids sur un corpus.

Il repose sur un assemblage de structures et de procédures. Au lieu d'apprendre par défaut en modifiant des paramètres neuronaux, il peut, suivant la fonction considérée :

- enrichir un lexique et ses relations ;
- acquérir une nouvelle règle ou une nouvelle correspondance de traduction ;
- accepter une nouvelle compétence spécialisée par contrat ;
- retenir une expérience vérifiée et ses conditions ;
- distinguer un fait d'une hypothèse ;
- réviser une relation contestée ;
- réorganiser des voies de recherche et des priorités de mémoire ;
- réemployer une preuve ou un calcul validé ;
- expliquer ce qu'il a fait et ce qu'il ne sait pas faire.

**Ce n'est pas une intelligence qui aurait besoin de connaître d'avance toutes les réponses.** Elle doit disposer de principes de traitement suffisants pour construire des réponses nouvelles à partir de relations et d'opérations disponibles. C'est cette capacité de généralisation structurelle que le projet cherche à développer et à mesurer.

Elle ne dispense pas d'acquérir de l'information. Une grammaire a besoin de règles, un vocabulaire a besoin d'entrées, un calculateur a besoin d'opérations, un modèle du monde a besoin d'observations. Mais **acquérir des informations ou intégrer un outil n'est pas synonyme d'entraîner un réseau neuronal**.

Des modèles déjà entraînés peuvent exister **à côté** de ce mécanisme : reconnaissance vocale, synthèse naturelle ou auxiliaire Qwen. Lorsqu'ils sont utilisés, ils doivent être identifiés comme tels. Leur présence facultative dans l'écosystème ne transforme pas le cœur natif en modèle pré-entraîné et ne doit pas être utilisée pour lui attribuer des compétences qu'il ne possède pas.

### Apprendre n'est pas accumuler

La trajectoire visée distingue **donnée → observation → expérience → hypothèse → connaissance → compétence → proposition → décision → action**. Les flèches ne sont pas des promotions automatiques. Chacune nécessite des conditions propres. Une expérience peut confirmer une hypothèse, la contredire ou rester inexploitable. Une nouvelle compétence peut être disponible sans être autorisée à agir.

C'est pourquoi l'éducation d'**Oxygen**, les mécanismes mémoriels et les contrôles de KX108 sont liés sans être confondus : l'évolution du savoir doit rester possible, et les frontières de l'autorité doivent rester explicites.

---

## 9 — La sobriété comme moteur de conception

Je n'avais pas les moyens de lancer un entraînement gigantesque, de maintenir une grappe de GPU ou de dépendre d'un centre de calcul pour chaque question. Je devais construire avec des machines ordinaires, peu de mémoire disponible, un stockage contraint et des ressources financières limitées.

Cette contrainte a transformé la manière d'aborder l'IA. Elle m'a conduit à demander, à chaque étape : **est-il nécessaire de dépenser de l'inférence pour cette opération, ou avons-nous déjà une structure, une règle, une preuve, une mémoire ou un outil capable de la résoudre directement ?**

Plusieurs économies se combinent :

1. **Économie de calcul** : traiter localement les règles et opérations déterministes.
2. **Économie de mémoire** : maintenir des représentations compactes et activer seulement les parties utiles.
3. **Économie de tokens** : ne pas verbaliser tout le travail interne pour obtenir un résultat.
4. **Économie de répétition** : réutiliser les acquis et calculs encore valides.
5. **Économie de développement** : retrouver une capacité existante avant d'en écrire une nouvelle.
6. **Économie de transfert** : éviter les copies massives lorsque des références et des interfaces suffisent.
7. **Économie d'énergie** : réveiller les moteurs lourds seulement lorsqu'ils apportent une valeur réelle.
8. **Économie de dépendance** : rendre le fonctionnement de base possible hors cloud et hors GPU dédié.

Ces économies ne se mesurent pas seulement en tokens. La métrique juste est le **coût d'une compréhension et d'une réponse réellement correctes, dans un cadre de ressources et de sûreté défini**.

Des démonstrateurs comme **AMD Router** ont exploré le routage local et la réduction d'appels inutiles. Ils constituent des indices techniques intéressants, mais le véritable objectif va plus loin : **une architecture dont la sobriété vient de son organisation, pas seulement d'une optimisation tardive**.

La possibilité de fonctionner sur de petits PC n'est pas une fonctionnalité secondaire. Elle exprime une volonté d'accessibilité : une intelligence utile ne devrait pas être réservée à ceux qui peuvent financer de très grands entraînements et une infrastructure permanente.

---

## Sécurité, éthique et Safe by Design — les conditions de l'intelligence

La sécurité et l'éthique ne sont pas une décoration ajoutée à Brody une fois qu'il sait parler. Elles font partie de la question qui a donné naissance à Obsidia : **comment permettre à une intelligence de comprendre, d'apprendre, de se transformer et d'interagir avec le réel, sans que l'extension de ses capacités provoque une extension incontrôlée de ses pouvoirs ?**

Il serait contradictoire de construire une intelligence qui distingue les faits des hypothèses, mais qui pourrait ensuite agir sur une hypothèse comme si elle était une autorisation. Il serait tout aussi contradictoire de rendre sa mémoire évolutive sans protéger les provenances, les consentements, les contradictions et les droits des personnes concernées.

### La sûreté est une propriété de l'architecture

Le principe **Safe by Design** signifie ici que les limites sont inscrites dans les contrats, les interfaces et les chemins d'exécution. Brody peut interpréter et proposer. Un moteur spécialisé peut calculer, comparer ou produire une preuve. Un organe de développement comme Obsidure peut préparer un changement. **Aucun de ces travaux ne devient, par sa seule qualité cognitive, un droit de décider ou d'agir.**

KX108 garde la frontière souveraine. Son rôle ne consiste pas à rendre Brody moins intelligent, mais à empêcher que l'intelligence soit confondue avec l'autorité. Les états d'admission, de réserve ou de refus — notamment `ACT`, `HOLD` et `BLOCK` selon les contrats applicables — matérialisent cette distinction. Une absence d'information, une preuve insuffisante, une permission manquante ou une incohérence doivent conserver leur statut, même si le système sait formuler une réponse persuasive.

La gouvernance n'est donc pas une phrase de consigne adressée à un modèle. Elle doit pouvoir être observée dans les chemins de données, les droits effectifs, les refus, les reçus et les tests négatifs. **Une interdiction qui disparaît lorsqu'on change d'interface n'est pas une protection structurelle.**

### Asimov : des principes répartis, pas une promesse morale

Les réflexions historiques autour des **lois d'Asimov distribuées** posent un problème essentiel : une intelligence ne doit pas devenir sûre uniquement parce qu'elle déclare vouloir respecter une règle. Des principes de protection doivent être traduits en contraintes vérifiables, réparties entre les couches, avec leurs propres responsabilités et leurs points d'arrêt.

L'objectif n'est pas de prétendre que trois formules littéraires résolvent toutes les questions éthiques. Il est de demander comment une intention, un risque, une conséquence possible et une interdiction peuvent être **représentés, transmis et contrôlés sans dépendre de la bonne volonté d'un seul organe**. Les contraintes peuvent ainsi rester applicables lorsqu'un moteur est remplacé, lorsqu'une nouvelle compétence entre dans l'organisme ou lorsqu'un mode de dialogue change.

Cette distribution oblige aussi à reconnaître les limites des règles. Deux protections peuvent entrer en tension ; une conséquence peut rester inconnue ; une situation peut être trop ambiguë pour qu'une action soit admise. L'architecture doit alors conserver la tension ou suspendre l'action plutôt que fabriquer une certitude artificielle.

### Préserver les droits pendant la traduction du sens

La séparation des pouvoirs serait inutile si une traduction pouvait changer silencieusement le statut de ce qu'elle transporte. C'est pourquoi **OS Trad, OS Trad Uni, Reverse OS et les IR** appartiennent aussi à la sûreté du système.

Une demande en français, en anglais ou en mandarin, un concept Hanzi, un graphe, une mesure, une formule ou une primitive informatique ne portent pas spontanément les mêmes garanties. À chaque passage, il faut conserver les éléments dont dépend la fidélité : provenance, type, négation, condition, incertitude, unité, temporalité, autorisation et portée de l'affirmation.

**Traduire une intention n'autorise pas son exécution.** Convertir une proposition en IR ne la transforme pas en ordre. Rendre un résultat lisible ne le transforme pas en fait prouvé. Une représentation plus compacte ne peut pas effacer une restriction de confidentialité ou augmenter les droits du consommateur suivant.

Quand la correspondance est incertaine ou impossible, le chemin fidèle doit permettre de déclarer l'inconnu, demander une précision, conserver plusieurs interprétations ou refuser le passage. La traduction inverse doit restituer ces limites dans une langue compréhensible par l'humain, plutôt que les masquer derrière une formulation fluide.

### Une éthique de la connaissance, de la mémoire et de l'apprentissage

Le cœur natif de Brody est conçu **sans entraînement neuronal préalable**. Cela ne signifie pas qu'il n'a besoin ni de données ni de connaissances. Cela signifie que l'acquisition et l'évolution peuvent être organisées autrement : par observation, mise en relation, représentation, vérification, mémoire et révision de structures explicites.

Cette voie donne une responsabilité particulière à la mémoire. Enregistrer une phrase ne suffit pas pour en faire une vérité. Déduire une relation ne suffit pas pour en faire une expérience vécue. Une source externe ne doit pas être confondue avec un souvenir personnel ; une corrélation avec une causalité ; une contradiction avec une erreur à effacer.

La mémoire cognitive recherchée — graphes natifs, représentations multidimensionnelles, expériences, ARS/ARD, AVDR, traces, oubli actif et mémoire négative — doit pouvoir maintenir **ce qui est connu, ce qui a été inféré, ce qui a été réfuté, ce qui est contesté et ce qui reste inconnu**. Elle doit aussi respecter la vie privée, le consentement, la minimisation des données, la confidentialité et les droits associés aux sources. Le droit de se souvenir n'est pas un droit illimité de collecter ou de divulguer.

L'oubli lui-même ne doit pas devenir une suppression opportuniste des erreurs ou des preuves. Il doit être pensé avec la provenance, la conservation nécessaire, les droits de retrait et la possibilité d'audit. De même, une compétence nouvellement acquise peut être techniquement utilisable sans devenir automatiquement autorisée.

### L'évolution sans mutation de l'autorité

L'organisme doit pouvoir accueillir un nouveau moteur, une grammaire plus riche, une expérience ou un domaine inconnu sans réécrire son noyau à chaque progrès. C'est la promesse architecturale du cadre *ex ante*. Mais **l'accueil d'une capacité n'est pas sa promotion au rang d'autorité**.

Les invariants de gouvernance, les frontières de lecture et d'écriture, les validations humaines lorsqu'elles sont requises, la réversibilité des changements et les contrôles de non-régression sont destinés à survivre à cette évolution. Un moteur auxiliaire, même capable de donner une bonne réponse ou d'écrire un programme correct, ne reçoit pas par ce fait une permission de modifier KX108, de publier ou d'agir sur le monde.

Les démonstrateurs, preuves formelles et tests de refus sont importants pour vérifier ce principe. Leur réussite n'autorise toutefois pas à déclarer toute la sûreté démontrée : chaque nouveau raccordement, nouvelle surface d'entrée et nouvelle capacité étendent ce qui doit être éprouvé.

### Une intelligence contestable, explicable et au service de l'humain

Je ne cherche pas une intelligence à laquelle l'humain devrait abandonner sa faculté de juger. Je cherche une intelligence capable d'aider à comprendre, apprendre, créer et décider, en laissant visibles les raisons, les limites et les alternatives de ce qu'elle propose.

Une conclusion doit pouvoir être contestée. Une erreur doit pouvoir être reconnue. Une décision humaine ne doit pas être déguisée en nécessité mathématique, et une suggestion machine ne doit pas se présenter comme un verdict souverain. La diversité des perspectives, l'accessibilité sur des machines ordinaires et la possibilité de fonctionner localement font aussi partie de cette exigence : la maîtrise d'une intelligence ne devrait pas dépendre entièrement d'une infrastructure distante et opaque.

**Le but est de faire grandir ensemble l'intelligence et les conditions de sa sûreté.** Chaque nouvelle capacité doit pouvoir entrer dans Obsidia sans que le système perde son sens, sa cohérence, sa responsabilité ou la place de l'humain. C'est une orientation de conception qui exige des preuves continues, et non une certification de sécurité déjà acquise.

---

## 10 — L'horizon : une intelligence qui accueille le monde sans se perdre

La finalité dépasse le simple dialogue bilingue et la réponse à des exercices. Je cherche une architecture capable de traverser des situations et des domaines sans reconstruire un cerveau entier à chaque passage.

Une intelligence capable de **recevoir**, **distinguer**, **relier**, **mémoriser**, **comparer**, **raisonner**, **vérifier**, **réviser** et **expliquer**. Une intelligence qui ne prend pas une relation symbolique pour un fait physique. Qui n'efface pas ses erreurs parce qu'elles gênent une histoire fluide. Qui ne prend pas une proposition pour une autorisation. Qui peut accueillir de nouveaux outils sans confondre leur langage avec le sien.

La recherche sur les **34 arbres, les dimensions, les nuages de points, ARS/ARD, les partitions, les fourmis et les abeilles** représente différentes façons d'organiser les relations et l'exploration. La recherche sur **OS Trad, Reverse OS, les IR et les symboles** concerne la circulation fidèle de la signification. **Oxygen** porte la question de l'éducation. **KX108** porte la frontière souveraine. **Brody** permet à cet ensemble de prendre une forme conversationnelle et compréhensible.

L'horizon **Oxygène 2026–2030**, avec ses jalons C0 à C9, inscrit cette idée dans une trajectoire de recherche, de démonstration locale, de coopération entre domaines et d'évolution de l'organisme. Cet horizon n'est ni une preuve d'AGI déjà obtenue ni une revendication de conscience artificielle. **L'organisme est une architecture fonctionnelle et un programme de recherche, pas une affirmation de vie subjective.**

La question ouverte demeure : **jusqu'où cette intelligence peut-elle évoluer par organisation des relations et expérience, sans dépendre de l'entraînement préalable d'un modèle géant ?**

Ce n'est pas une question à laquelle un README doit répondre par une promesse. C'est celle que l'architecture doit permettre de tester.

---

## 11 — Ce qui existe déjà : des preuves au service de la conception

Obsidia n'est pas seulement un projet écrit. Depuis février 2025, des organes, des règles, des tests et des prototypes ont été développés dans plusieurs dépôts. Les démonstrations servent à examiner une hypothèse de construction : **les fonctions peuvent exister séparément, être gouvernées et être rapprochées sans qu'un grand modèle entraîné les contienne toutes**.

Le Brody natif dispose de travaux sur la **grammaire FR/EN**, le **lexique relationnel**, la **réalisation linguistique**, l'**assemblage de contexte B6**, la **mémoire native en lecture**, la **suffisance des éléments disponibles**, le **raisonnement déductif et le calcul exact**, la **composition éditoriale** et les **interfaces vocales**. Certains éléments sont déjà testés de façon isolée ; d'autres ont été réunis dans un dépôt de convergence au cours de novembre 2026.

Dans l'écosystème plus large, des travaux de **preuve, de gouvernance, de calcul, d'intégration de domaines et de développement de code gouverné** illustrent la spécialisation des organes. Ils n'ont pas vocation à être copiés aveuglément à l'intérieur de Brody : leur contribution se définit par leurs contrats.

Les comptes rendus de convergence annoncent notamment :

- un socle portable ;
- des moteurs linguistiques natifs ;
- un rappel mémoire et un contexte B6 ;
- un moteur de raisonnement natif ;
- une composition éditoriale Studio E11 ;
- des interfaces vocales avec composants de substitution et moteurs optionnels.

**Ces résultats ne démontrent pas que la totalité de la vision est réalisée.** En particulier, la mémoire cognitive multidimensionnelle, l'exploration par essaims, toutes les transductions symboliques, l'éducation expérientielle et le traitement général de situations inédites doivent encore être examinés dans leurs contrats et leurs comportements réels.

Il faut lire les résultats avec une distinction constante :

| État | Ce que cela signifie |
|---|---|
| **Conçu** | Une idée, une structure ou un contrat ont été formulés |
| **Développé** | Un composant et son code existent |
| **Testé** | Un comportement a été vérifié dans un environnement donné |
| **Raccordé** | Le parcours Brody appelle ce composant |
| **Utilisé** | La capacité sert effectivement à résoudre des demandes |
| **Mesuré** | Sa contribution à l'autonomie, à la justesse et au coût est quantifiée |

Un grand nombre de tests verts ne remplace pas cette distinction. Un taux d'intégration de composants n'est pas une mesure d'intelligence. **Le vrai bilan sera celui des conversations résolues correctement par Brody sans auxiliaire neuronal, des limites qu'il sait reconnaître et de l'évolution qu'il peut réaliser sous contrôle.**

---

## 12 — Pourquoi un dépôt de convergence Brody

La construction s'est faite entre plusieurs ordinateurs, dépôts, branches, worktrees et archives. Cela a permis d'expérimenter sans casser tous les composants à chaque étape. Cela a aussi produit une difficulté : **la version la plus récente d'un fichier n'est pas nécessairement la version la plus complète d'une capacité**.

Le dépôt public de convergence a été créé pour **retrouver et réunir les meilleures capacités existantes de Brody**, sans refaire ce qui existe et sans effacer la provenance du travail. Il doit permettre à une personne extérieure de comprendre l'architecture, puis d'exécuter et d'évaluer progressivement le système réellement raccordé.

Le chemin de convergence comporte sept lots de travail : **socle, linguistique, mémoire native, raisonnement, composition, voix, orchestration conversationnelle et mesure de l'autonomie**. Ces lots sont des opérations d'intégration, pas les sept fondements de l'intelligence et encore moins la conclusion du programme de recherche.

Après leur assemblage, la vérification essentielle consistera à confronter le résultat aux sources originales — ordinateur fixe, portable, dépôts GitHub, variantes isolées, archives — et à déterminer précisément ce qui a été :

- retrouvé dans sa version la plus avancée ;
- raccordé sans perte de fonction ;
- seulement copié ou importé ;
- reconstruit à tort ;
- laissé dans un autre dépôt ;
- encore absent ou en conception.

Cette convergence doit **respecter les frontières de souveraineté** : KX108, Sigma, Obsidure, Monde et les autres organes conservent leurs responsabilités. Elle doit aussi préserver les travaux non commitées, les producteurs protégés, les mémoires privées et les sources historiques. **Un point central de référence n'exige pas de fusionner tous les dépôts en un seul monolithe.**

---

## 13 — Les étapes d'une recherche, pas une liste de fonctionnalités

L'histoire d'Obsidia suit une logique de découvertes successives :

**Février 2025 — Le doute fondateur.** Les premiers dossiers `AGI_A_FAIRE.txt` et les synthèses AGI posent le problème de l'intelligence, de la mémoire et de la coopération. Le projet commence avec les questions, pas avec un réseau neuronal déjà entraîné.

**Printemps 2025 — La cohérence et la pédagogie.** La calibration originelle, les lois, les 34 arbres, les réflexions sur les mémoires et la métaphore du moteur cherchent à donner une forme compréhensible et gouvernable à la vision.

**2025 — Les différents langages.** Les couches OS0–OS4, OS Trad, Reverse OS, les IR et les recherches symboliques apparaissent comme des moyens de relier des domaines qui ne se représentent pas le réel de la même manière.

**Fin 2025 – début 2026 — Le noyau et les frontières.** X-108/KX108, RTOS et les invariants structurent la séparation entre ce que les organes savent proposer et ce que le système est autorisé à faire.

**Printemps 2026 — Les domaines.** Les travaux Trinity, GPS/Aviation, Banque et Trading interrogent la possibilité de faire passer des spécialités différentes sous des contrats de gouvernance communs.

**Juin–juillet 2026 — La fidélité et Asimov distribué.** Les travaux d'interlangage, de non-promotion automatique, de sentinelles et de preuves formelles précisent les conditions de circulation des informations.

**Août–octobre 2026 — L'économie et l'éducation.** AMD Router et Oxygen portent les questions de sobriété, d'émergence fonctionnelle, de progression et de réutilisation des capacités.

**Novembre 2026 — La convergence et la mémoire cognitive.** L'inventaire des variantes Brody et le plan des huit fondations mémorielles rappellent la différence entre un runtime déjà fonctionnel et la destination cognitive complète.

Ce récit historique n'attribue pas automatiquement à chaque période une implémentation achevée. Les concepts ont mûri, changé de nom ou reçu plusieurs variantes. Il faut préserver leurs documents et leurs traces sans en inventer une continuité parfaite après coup.

---

## 14 — Sources fondatrices et méthode de vérité

Cette conception doit pouvoir être reliée à ses sources. Les archives originales ne sont pas nécessairement publiques, mais leurs noms permettent de retrouver les étapes et les décisions :

| Famille | Sources historiques de référence |
|---|---|
| **Acte fondateur** | `AGI_A_FAIRE.txt`, `Synthèse_Obsidia_AGI.docx`, `dossier_AGI_final_avec_metriques.txt` |
| **Sens et cohérence** | `Obsidia_Rituel_Calibration_Originelle_Etienne.docx`, `Obsidia_Chapitre_12_Lois_Obsidiennes_FINAL.docx`, `VULGARISATION_BRODY.txt` |
| **OS et interlangage** | `ARCHITECTURE_PROTOCOL_OS.txt`, `REVERSE_OS_ELOQUENCE.txt`, `ALPHABET_IR_AGENT_VECTEUR.txt`, `REVERSE_OS_INTERLANGUAGE_CANON_V1` |
| **Mémoire et organisation** | `CERVEAU_OBSIDIA.txt`, `FONDATEURS_PHILOSOPHIE.txt`, plan des huit fondations de mémoire cognitive |
| **Autorité et limites** | `CAPABILITY_IS_NOT_AUTHORITY_V1.md`, `BRODY_GPT_V1_LIMITATIONS_AND_BOUNDARIES.md`, preuves et contrats KX108 |
| **Évolution et sobriété** | Correspondances historiques sur Oxygen, Asimov, AMD Router et l'économie d'inférence |
| **Réalisation** | Inventaires de capacités, sources de code, manifests Git, rapports AGY de convergence et suites de tests |

Les échanges Gmail et les documents Drive ont contribué à la reconstruction de l'origine : notamment les réflexions de juillet 2026 sur Asimov distribué et les 34 dimensions, celles d'août sur Oxygen et l'économie, et le plan mémoriel du 18 novembre 2026. Ces sources conservent leur statut d'archives : **un texte de conception peut expliquer une intention sans prouver l'existence d'un moteur exécuté**.

Les preuves techniques doivent être rattachées à des commits, à des versions de contrats, à des tests et à des conditions d'exécution. Le projet conserve le droit de dire **« conçu mais non raccordé »**, **« démontré dans un banc limité »**, **« contradictoire »** ou **« inconnu »**. Cette honnêteté est une condition de son ambition.

---

## Ce que je cherche finalement à démontrer

Je ne veux pas seulement une machine qui parle. Je veux comprendre **comment une intelligence peut être construite à partir des langages, des relations, des structures, des expériences et des capacités déjà possibles**, sans devoir les enfermer au préalable dans un même modèle neuronal entraîné.

Je veux que la machine puisse travailler dans ses langages propres, passer de l'un à l'autre, conserver le sens, ne pas oublier les contradictions, apprendre de ce qui a été réellement éprouvé, accueillir de nouvelles facultés et expliquer ce qu'elle fait.

Je veux qu'elle puisse fonctionner **sur des ordinateurs ordinaires**, parce que l'intelligence ne devrait pas être conditionnée uniquement par l'argent, la puissance de calcul ou l'accès permanent à un fournisseur extérieur.

Je veux qu'elle soit capable **d'avancer sans prétendre savoir ce qu'elle ignore**, et que sa capacité à raisonner reste distincte de son droit d'agir.

**Brody est l'expression de cette recherche dans la conversation. Obsidia est l'architecture d'accueil, de traduction, de mémoire, de calcul et de gouvernance qui lui donne sa profondeur.**

Le projet n'est pas terminé parce que des modules réussissent des tests. Il progressera lorsque ces mécanismes, réunis, sauront résoudre des situations inédites, justifier leurs conclusions, apprendre dans les frontières prévues et rester cohérents en changeant d'échelle.

> **Je n'ai pas commencé en sachant construire cette intelligence. J'ai commencé en cherchant les bonnes questions. Puis j'ai construit l'architecture pour accueillir les réponses, même celles que je ne connaissais pas encore.**

— **Etienne Aubin**, fondateur d'Obsidia et concepteur de Brody

*Document fondateur — proposition V3 soumise à validation humaine. Aucune publication ni modification du dépôt distant n'est impliquée par cette rédaction.*
