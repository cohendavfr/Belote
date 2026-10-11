# Belote

Belote en Python, dans le terminal : vous et Partenaire contre Ouest et Est (3 bots). Deux modes : **belote contrat** (par défaut) et **coinche**.

## Jouer dans le navigateur

Ouvrir `index.html` dans un navigateur (aucune dépendance, tout est dans le fichier) : table graphique, belote contrat ou coinche, bots simples ou malins. C'est le même moteur que `belote.py`, porté en JavaScript. Les joueurs annoncent leurs enchères à voix haute (français, anglais, espagnol ou japonais, au choix) avec 2 secondes de silence entre chaque annonce, puis le donneur annonce le contrat retenu, grâce à la synthèse vocale du navigateur ; la qualité des voix dépend du système.

## Jouer en ligne (2 à 4 joueurs)

Dans le menu, « Créer une salle » donne un code de 5 caractères ; les autres joueurs le saisissent dans « Rejoindre ». Les places libres sont tenues par des bots du niveau choisi par l'hôte, et chacun peut changer de place avant le lancement (les deux places d'une équipe sont face à face).

- Deux voies indépendantes, la salle s'ouvre dès que l'une répond : une connexion directe entre navigateurs (WebRTC, via PeerJS) et un serveur de messages public (MQTT sur WebSocket sécurisé, trois serveurs interrogés en parallèle). Chaque joueur utilise celle qui marche pour lui, ce qui fonctionne depuis un téléphone en 4G/5G ou derrière un pare-feu. Les serveurs publics sont parfois lents : la création d'une salle peut prendre quelques secondes
- L'hôte fait tourner la partie ; chaque joueur ne reçoit que sa propre main. Le code de la salle sert de secret : ne le diffusez pas publiquement
- Bouton « Quitter la partie » à côté de « Nouvelle partie » (en ligne) : les autres joueurs voient un avis sur le tapis et dans le journal, et un bot prend la place. Si l'hôte quitte, la salle se ferme pour tous avec son nom. Un joueur déconnecté est aussi signalé et remplacé par un bot
- L'hôte est aussi un joueur : il connaît techniquement toutes les mains, c'est un jeu entre amis
- Les annonces vocales sont jouées sur chaque navigateur, dans la langue choisie par chacun
- Voix et vidéo : chaque joueur peut activer son micro et/ou sa caméra (deux petits boutons sur votre vignette, à côté de votre nom sur la table, et dans la salle d'attente). Les flux passent directement d'un navigateur à l'autre (WebRTC) quand ils aboutissent. Si la connexion directe ne passe pas (4G, pare-feu), le jeu bascule automatiquement en mode allégé : le son (8 kHz) et une petite image toutes les 0,4 s transitent par le même serveur de messages que le jeu. Qualité téléphone, mais ça passe partout ; un message l'indique. Chaque joueur a une vignette à côté de son nom : sa vidéo, ou une tête grisée s'il n'a pas de caméra ; elle s'entoure d'un liseré doré quand il parle ; le micro et la caméra restent éteints tant que vous ne les activez pas

## Lancer en terminal

```bash
python3 belote.py                  # belote contrat, jusqu'à 1000 points
python3 belote.py --coinche        # mode coinche
python3 belote.py --cible 500      # autre score cible
python3 belote.py --bots malin      # bots moins forts (expert par défaut, simple aussi possible)
python3 belote.py --auto --seed 1  # 4 bots jouent entre eux (reproductible)
python3 -m unittest -v             # tests
```

## Règles communes

- Sens de jeu anti-horaire : le premier à parler et à jouer est le joueur à droite du donneur (Vous → Est → Partenaire → Ouest)
- Jeu de 32 cartes, valeurs atout / hors atout, dix de der (+10), belote-rebelote (+20)
- Jeu des plis : fournir, couper (sauf si le partenaire est maître), surcouper / monter à l'atout

## Belote contrat

- 5 cartes distribuées, carte retournée, enchères en 2 tours, puis 3 cartes (2 pour le preneur qui reçoit la retournée)
- Le preneur doit marquer plus que ses adversaires, sinon « chute » (162 points pour la défense)
- Capot : +90

## Coinche

- 8 cartes distribuées, enchères au point : 80 à 160 par 10, puis capot (250) ; fin après 3 passes
- Les adversaires du preneur peuvent **coincher** (x2), le preneur peut **surcoincher** (x4)
- Contrat rempli (belote comprise) : sans coinche, le preneur marque ses points + le contrat, la défense ses points ; avec coinche, le preneur marque (162 + contrat) × multiplicateur
- Contrat chuté : la défense marque (162 + contrat) × multiplicateur
- Capot : le preneur doit gagner les 8 plis

## Bots

- **expert** (par défaut) : joue comme le malin, et en plus :
  - il simule des donnes plausibles à partir de ce qu'il a le droit de savoir (sa main, les cartes jouées, les couleurs que chacun n'a pas fournies, les enchères) puis joue la carte qui rapporte le plus en moyenne ; il ne voit jamais les mains des autres
  - il fait et lit des **appels** : en défaussant hors atout, une carte forte (10, Roi, Dame) demande à son partenaire de rejouer cette couleur, une carte faible (7, 8) la refuse. Vous pouvez utiliser la même convention avec votre partenaire bot
- **malin** : se souvient des cartes jouées, repère les cartes maîtresses, tire les atouts en attaque, charge quand le partenaire est maître, soutient son partenaire aux enchères
- **simple** : heuristiques sans mémoire

Mesures sur des donnes identiques jouées dans les deux sens (points d'écart par donne) : expert contre malin, +14 ± 1,4 en belote contrat et +17 ± 2,6 en coinche ; malin contre simple, environ +14.

## À faire

- Tenir compte des enchères (qui a passé) dans les simulations
- Annonce « générale » en coinche
- Annonces de coinche « générale »
