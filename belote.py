"""Belote contrat ou coinche à 4 joueurs : vous (0) et Partenaire (2) contre Ouest (1) et Est (3)."""
import argparse
import random

COULEURS = ["Coeur", "Carreau", "Trefle", "Pique"]
SYMBOLES = {"Coeur": "♥", "Carreau": "♦", "Trefle": "♣", "Pique": "♠"}
VALEURS = ["7", "8", "9", "10", "Valet", "Dame", "Roi", "As"]

POINTS_ATOUT = {"7": 0, "8": 0, "9": 14, "10": 10, "Valet": 20, "Dame": 3, "Roi": 4, "As": 11}
POINTS_HORS_ATOUT = {"7": 0, "8": 0, "9": 0, "10": 10, "Valet": 2, "Dame": 3, "Roi": 4, "As": 11}

# Du plus faible au plus fort
ORDRE_ATOUT = ["7", "8", "Dame", "Roi", "10", "As", "9", "Valet"]
ORDRE_PLAIN = ["7", "8", "9", "Valet", "Dame", "Roi", "10", "As"]

NOMS = ["Vous", "Ouest", "Partenaire", "Est"]
EQUIPES = ["Vous + Partenaire", "Ouest + Est"]
BONUS_DIX_DE_DER = 10
BONUS_BELOTE = 20
BONUS_CAPOT = 90
TOTAL_CARTES = 162
ENCHERES = [80, 90, 100, 110, 120, 130, 140, 150, 160, 250]  # 250 = capot
CAPOT = 250


def nom_contrat(valeur):
    return "Capot" if valeur == CAPOT else str(valeur)


def apres(depart, n):
    """Joueur situé n places après `depart` : on tourne dans le sens anti-horaire."""
    return (depart + 3 * n) % 4


def creer_jeu():
    return [(valeur, couleur) for couleur in COULEURS for valeur in VALEURS]


def nom_carte(carte):
    return f"{carte[0]}{SYMBOLES[carte[1]]}"


def points(carte, atout):
    valeur, couleur = carte
    return (POINTS_ATOUT if couleur == atout else POINTS_HORS_ATOUT)[valeur]


def force(carte, atout, demandee):
    """Force d'une carte dans un pli : atout > couleur demandée > rien."""
    valeur, couleur = carte
    if couleur == atout:
        return 100 + ORDRE_ATOUT.index(valeur)
    if couleur == demandee:
        return ORDRE_PLAIN.index(valeur)
    return -1


def gagnant_pli(pli, atout):
    """pli : liste de (joueur, carte) dans l'ordre de jeu. Renvoie le joueur gagnant."""
    demandee = pli[0][1][1]
    return max(pli, key=lambda jc: force(jc[1], atout, demandee))[0]


def cartes_jouables(main, pli, atout):
    """Règles : fournir, sinon couper (sauf si le partenaire est maître), monter à l'atout."""
    if not pli:
        return list(main)
    demandee = pli[0][1][1]
    meilleure = max(force(c, atout, demandee) for _, c in pli)

    meme_couleur = [c for c in main if c[1] == demandee]
    if meme_couleur:
        if demandee == atout:
            plus_fortes = [c for c in meme_couleur if force(c, atout, demandee) > meilleure]
            return plus_fortes or meme_couleur
        return meme_couleur

    joueur = apres(pli[0][0], len(pli))
    if gagnant_pli(pli, atout) == (joueur + 2) % 4:
        return list(main)

    atouts = [c for c in main if c[1] == atout]
    if atouts:
        plus_forts = [c for c in atouts if force(c, atout, demandee) > meilleure]
        return plus_forts or atouts
    return list(main)


def charge(jouables, atout, demandee):
    """Partenaire maître : on charge de points, mais sans gaspiller d'atout si on peut se défausser."""
    hors = [c for c in jouables if c[1] != atout]
    pool = hors if hors and not any(c[1] == demandee for c in jouables) else jouables
    return max(pool, key=lambda c: (points(c, atout), -force(c, atout, c[1])))


ORDRE_MAIN = ["Coeur", "Trefle", "Carreau", "Pique"]


def trier_main(main, atout=None):
    """♥ ♣ ♦ ♠ de gauche à droite, valeurs décroissantes (ordre des atouts pour l'atout)."""
    def cle(c):
        suite = ORDRE_ATOUT if c[1] == atout else ORDRE_PLAIN
        return (ORDRE_MAIN.index(c[1]), -suite.index(c[0]))
    return sorted(main, key=cle)


def afficher_main(main, atout=None):
    return "  ".join(nom_carte(c) for c in trier_main(main, atout))


# --- Joueurs -----------------------------------------------------------------

class Bot:
    """Bot simple : aucune mémoire des plis précédents."""

    def debut_donne(self, moi, atout, preneur, contrat=None, mult=1):
        self.moi, self.atout, self.preneur = moi, atout, preneur

    def valeur_main(self, main, couleur):
        cartes = [c for c in main if c[1] == couleur]
        total = sum(POINTS_ATOUT[v] for v, _ in cartes)
        if len(cartes) >= 3:
            total += 10
        total += 5 * sum(1 for v, c in main if v == "As" and c != couleur)
        return total

    def prise(self, main, retournee, tour):
        if tour == 1:
            candidats = [retournee[1]]
            main = main + [retournee]
            seuil = 38
        else:
            candidats = [c for c in COULEURS if c != retournee[1]]
            seuil = 34
        meilleur = max(candidats, key=lambda c: self.valeur_main(main, c))
        return meilleur if self.valeur_main(main, meilleur) >= seuil else None

    def estimation(self, main, couleur):
        """Contrat qu'on espère réaliser avec cette couleur, arrondi à la dizaine."""
        return min(160, (40 + self.valeur_main(main, couleur)) // 10 * 10)

    def enchere(self, main, courant, p):
        """courant = (valeur, couleur, joueur) ou None. Renvoie (valeur, couleur) ou None."""
        if courant is not None and courant[2] % 2 == p % 2:
            return None
        minimum = 80 if courant is None else next((v for v in ENCHERES if v > courant[0]), None)
        if minimum is None or minimum == CAPOT:
            return None
        couleur = max(COULEURS, key=lambda c: self.estimation(main, c))
        return (minimum, couleur) if self.estimation(main, couleur) >= minimum else None

    def coinche(self, main, contrat):
        valeur, couleur, _ = contrat
        atouts = [v for v, c in main if c == couleur]
        as_ = sum(1 for v, c in main if v == "As" and c != couleur)
        if valeur < 90:
            return False
        return ("Valet" in atouts and "9" in atouts) or ("Valet" in atouts and as_ >= 1 and len(atouts) >= 2)

    def surcoinche(self, main, contrat):
        valeur, couleur, _ = contrat
        return self.estimation(main, couleur) >= valeur + 20

    def choisir_carte(self, main, jouables, pli, atout, vus=()):
        if len(jouables) == 1:
            return jouables[0]
        demandee = pli[0][1][1] if pli else None
        if not pli:
            atouts = [c for c in jouables if c[1] == atout]
            if ("Valet", atout) in atouts:
                return ("Valet", atout)
            as_ = [c for c in jouables if c[0] == "As" and c[1] != atout]
            if as_:
                return as_[0]
            return min(jouables, key=lambda c: (points(c, atout), force(c, atout, c[1])))
        courant = gagnant_pli(pli, atout)
        joueur = apres(pli[0][0], len(pli))
        if courant == (joueur + 2) % 4:
            return charge(jouables, atout, demandee)
        meilleure = max(force(c, atout, demandee) for _, c in pli)
        gagnantes = [c for c in jouables if force(c, atout, demandee) > meilleure]
        if gagnantes:
            return min(gagnantes, key=lambda c: force(c, atout, demandee))
        return min(jouables, key=lambda c: (points(c, atout), force(c, atout, demandee)))


class BotMalin(Bot):
    """Bot avec mémoire des cartes jouées, cartes maîtresses, jeu en attaque/défense."""

    def valeur_main(self, main, couleur):
        total = super().valeur_main(main, couleur)
        atouts = {v for v, c in main if c == couleur}
        if "Valet" in atouts and "9" in atouts:
            total += 10
        if "Roi" in atouts and "Dame" in atouts:
            total += 10
        if len(atouts) >= 5:
            total += 10
        return total

    def enchere(self, main, courant, p):
        if courant is not None and courant[2] % 2 == p % 2:
            return self.soutien(main, courant)
        return super().enchere(main, courant, p)

    def soutien(self, main, courant):
        """Relève le contrat du partenaire quand on a de bons atouts."""
        valeur, couleur, _ = courant
        atouts = {v for v, c in main if c == couleur}
        suivant = next((v for v in ENCHERES if v > valeur), None)
        if suivant is None or suivant > 120:
            return None
        aces = sum(1 for v, c in main if v == "As" and c != couleur)
        force_atouts = sum(POINTS_ATOUT[v] for v in atouts)
        if len(atouts) >= 2 and ("Valet" in atouts or "9" in atouts) and force_atouts + 5 * aces >= 30:
            return suivant, couleur
        return None

    @staticmethod
    def est_maitre(carte, atout, connues, main):
        couleur = carte[1]
        ordre = ORDRE_ATOUT if couleur == atout else ORDRE_PLAIN
        hautes = [(v, couleur) for v in ordre[ordre.index(carte[0]) + 1:]]
        return all(h in connues or h in main for h in hautes)

    def choisir_carte(self, main, jouables, pli, atout, vus=(), connues=None):
        if len(jouables) == 1:
            return jouables[0]
        if connues is None:
            connues = {c for _, c in vus}
        connues = connues | {c for _, c in pli}
        atouts_dehors = [(v, atout) for v in ORDRE_ATOUT
                         if (v, atout) not in connues and (v, atout) not in main]
        moi = apres(pli[0][0], len(pli)) if pli else self.moi
        attaquant = self.preneur % 2 == moi % 2

        if not pli:
            return self.entame(main, jouables, atout, connues, atouts_dehors, attaquant)

        demandee = pli[0][1][1]
        courant = gagnant_pli(pli, atout)
        meilleure = max(force(c, atout, demandee) for _, c in pli)
        dernier = len(pli) == 3
        if courant == (moi + 2) % 4:
            carte_partenaire = next(c for j, c in pli if j == courant)
            sur = dernier or (
                self.est_maitre(carte_partenaire, atout, connues, main)
                and (carte_partenaire[1] == atout or not atouts_dehors)
            )
            if sur:
                return charge(jouables, atout, demandee)
            return min(jouables, key=lambda c: (points(c, atout), force(c, atout, c[1])))

        gagnantes = [c for c in jouables if force(c, atout, demandee) > meilleure]
        if gagnantes:
            enjeu = sum(points(c, atout) for _, c in pli)
            coupe = gagnantes[0][1] == atout and demandee != atout
            if not coupe or dernier or enjeu >= 10:
                return min(gagnantes, key=lambda c: force(c, atout, demandee))
        return min(jouables, key=lambda c: (points(c, atout), force(c, atout, c[1])))

    def entame(self, main, jouables, atout, connues, atouts_dehors, attaquant):
        """Entame : l'attaquant tire d'abord les atouts adverses, puis encaisse ses cartes maîtresses ;
        le défenseur évite d'ouvrir à l'atout et prépare une coupe dans une couleur courte."""
        mes_atouts = [c for c in jouables if c[1] == atout]
        if attaquant and atouts_dehors:
            maitres = [c for c in mes_atouts if self.est_maitre(c, atout, connues, main)]
            if maitres:
                return max(maitres, key=lambda c: force(c, atout, atout))
            # Long en atouts sans le maître : un petit atout fait tomber les honneurs adverses.
            if len([c for c in main if c[1] == atout]) >= 4 and mes_atouts:
                return min(mes_atouts, key=lambda c: force(c, atout, atout))
        maitres = [c for c in jouables if c[1] != atout and self.est_maitre(c, atout, connues, main)]
        if maitres:
            return max(maitres, key=lambda c: points(c, atout))
        pool = [c for c in jouables if c[1] != atout] or jouables
        longueur = {couleur: sum(1 for c in main if c[1] == couleur) for couleur in COULEURS}
        sens = -1 if attaquant else 1   # attaque : couleur longue ; défense : couleur courte (pour couper)
        return min(pool, key=lambda c: (points(c, atout), sens * longueur[c[1]], force(c, atout, c[1])))


class BotExpert(BotMalin):
    """Bot malin qui simule des donnes plausibles, lit les appels du partenaire et en envoie.

    Il n'utilise que des informations publiques : sa main, les cartes déjà jouées (donc les
    couleurs que chacun n'a pas fournies) et les enchères. Il ne voit jamais les mains des autres.

    Convention d'appel (valable aussi pour vous, avec votre partenaire bot) : en défaussant hors
    atout, une carte forte (10, Roi, Dame) dans une couleur demande de la rejouer, une carte
    faible (7, 8) la refuse.
    """

    APPELS = ("10", "Roi", "Dame")
    REFUS = ("7", "8")
    ECHANTILLONS = 40   # donnes simulées par décision (mesuré : plus c'est élevé, meilleur est le jeu)
    MARGE = 0.5         # en points : sous cet écart, on préfère la carte qui envoie un signal

    # --- Lecture des informations publiques --------------------------------------
    @staticmethod
    def decouper_plis(vus, pli):
        plis = [list(vus[i:i + 4]) for i in range(0, len(vus), 4)]
        if pli:
            plis.append(list(pli))
        return plis

    def signaux(self, vus, pli, atout):
        """Lit les défausses publiques. Renvoie {joueur: {"appel": {couleurs}, "refus": {couleurs}}}."""
        signaux = {j: {"appel": set(), "refus": set()} for j in range(4)}
        for t in self.decouper_plis(vus, pli):
            demandee = t[0][1][1]
            for joueur, (valeur, couleur) in t[1:]:
                if couleur in (demandee, atout):
                    continue
                if valeur in self.APPELS:
                    signaux[joueur]["appel"].add(couleur)
                    signaux[joueur]["refus"].discard(couleur)
                elif valeur in self.REFUS:
                    signaux[joueur]["refus"].add(couleur)
                    signaux[joueur]["appel"].discard(couleur)
        return signaux

    def couleurs_vides(self, vus, pli, atout):
        """Couleurs qu'un joueur n'a plus, déduites de ce qu'il n'a pas fourni."""
        vides = {j: set() for j in range(4)}
        for t in self.decouper_plis(vus, pli):
            demandee = t[0][1][1]
            for i, (joueur, (_, couleur)) in enumerate(t):
                if i == 0 or couleur == demandee:
                    continue
                vides[joueur].add(demandee)
                # Il devait couper si le partenaire n'était pas maître : sans coupe, plus d'atout.
                if couleur != atout and gagnant_pli(t[:i], atout) != (joueur + 2) % 4:
                    vides[joueur].add(atout)
        return vides

    # --- Simulation ---------------------------------------------------------------
    def repartir(self, inconnues, besoins, vides, favorables, moi):
        """Répartit au hasard les cartes inconnues en respectant les couleurs vides."""
        for _ in range(25):
            cartes = inconnues[:]
            random.shuffle(cartes)
            cartes.sort(key=lambda c: sum(1 for j in besoins if c[1] in vides[j]), reverse=True)
            mains = {j: [] for j in besoins}
            reste = dict(besoins)
            ok = True
            for c in cartes:
                eligibles = [j for j in reste if reste[j] > 0 and c[1] not in vides[j]]
                if not eligibles:
                    ok = False
                    break
                j = random.choice(eligibles)
                mains[j].append(c)
                reste[j] -= 1
            if ok:
                return mains
        # Dernier recours : répartition sans contrainte (ne devrait presque jamais arriver).
        cartes = inconnues[:]
        random.shuffle(cartes)
        mains, i = {}, 0
        for j, n in besoins.items():
            mains[j] = cartes[i:i + n]
            i += n
        return mains

    def poids_echantillon(self, mains, signaux, atout, partenaire):
        """Les mains compatibles avec les appels du partenaire sont plus vraisemblables."""
        w = 1.0
        main = mains.get(partenaire, [])
        for couleur in signaux[partenaire]["appel"]:
            if any(c[1] == couleur and c[0] in ("As", "10", "Roi") for c in main):
                w *= 3.0
        for couleur in signaux[partenaire]["refus"]:
            if any(c[1] == couleur and c[0] == "As" for c in main):
                w *= 0.3
        return w

    def jouer_fin(self, mains, pli, atout, vus=()):
        """Termine la donne avec la politique malin. Renvoie (points, plis) de chaque équipe à partir de maintenant."""
        pol = BotMalin()
        pol.atout, pol.preneur = atout, self.preneur
        connues = {c for _, c in vus}
        gain, plis = [0, 0], [0, 0]
        pli = list(pli)
        while True:
            while len(pli) < 4:
                j = apres(pli[0][0], len(pli))
                jouables = cartes_jouables(mains[j], pli, atout)
                if len(jouables) == 1:
                    carte = jouables[0]
                else:
                    pol.moi = j
                    carte = pol.choisir_carte(mains[j], jouables, pli, atout, (), connues)
                mains[j].remove(carte)
                pli.append((j, carte))
            gagnant = gagnant_pli(pli, atout)
            g = sum(points(c, atout) for _, c in pli)
            fini = all(not m for m in mains.values())
            if fini:
                g += BONUS_DIX_DE_DER
            gain[gagnant % 2] += g
            plis[gagnant % 2] += 1
            if fini:
                return gain, plis
            connues.update(c for _, c in pli)
            jouables = list(mains[gagnant])
            if len(jouables) == 1:
                carte = jouables[0]
            else:
                pol.moi = gagnant
                carte = pol.choisir_carte(mains[gagnant], jouables, [], atout, (), connues)
            mains[gagnant].remove(carte)
            pli = [(gagnant, carte)]

    def evaluer(self, main, jouables, pli, atout, vus, moi, signaux):
        """Points moyens de notre équipe pour chaque carte jouable, sur des donnes plausibles."""
        joues = {c for _, c in vus} | {c for _, c in pli}
        inconnues = [c for c in creer_jeu() if c not in joues and c not in main]
        deja = {j: 0 for j in range(4)}
        for j, _ in list(vus) + list(pli):
            deja[j] += 1
        besoins = {j: 8 - deja[j] for j in range(4) if j != moi}
        if sum(besoins.values()) != len(inconnues):
            return None
        vides = self.couleurs_vides(vus, pli, atout)
        partenaire = (moi + 2) % 4
        eq = moi % 2
        totaux = {c: 0.0 for c in jouables}
        somme_poids = 0.0
        for _ in range(self.ECHANTILLONS):
            mains = self.repartir(inconnues, besoins, vides, None, moi)
            w = self.poids_echantillon(mains, signaux, atout, partenaire)
            somme_poids += w
            for c in jouables:
                simul = {j: list(m) for j, m in mains.items()}
                simul[moi] = [x for x in main if x != c]
                gain, _plis = self.jouer_fin(simul, list(pli) + [(moi, c)], atout, vus)
                totaux[c] += w * gain[eq]
        return {c: t / somme_poids for c, t in totaux.items()}

    # --- Choix de la carte ---------------------------------------------------------
    def choisir_carte(self, main, jouables, pli, atout, vus=()):
        if len(jouables) == 1:
            return jouables[0]
        connues = {c for _, c in vus} | {c for _, c in pli}
        dehors = [(v, atout) for v in ORDRE_ATOUT if (v, atout) not in connues and (v, atout) not in main]
        moi = apres(pli[0][0], len(pli)) if pli else self.moi
        attaquant = self.preneur % 2 == moi % 2
        signaux = self.signaux(vus, pli, atout)
        if pli:
            heuristique = self.suivre(main, jouables, pli, atout, connues, dehors, moi)
        else:
            heuristique = self.entame_experte(main, jouables, atout, connues, dehors, attaquant, moi, signaux)
        scores = self.evaluer(main, jouables, pli, atout, vus, moi, signaux)
        if not scores:
            return heuristique
        meilleur = max(scores.values())
        if scores[heuristique] >= meilleur - self.MARGE:
            return heuristique
        return max(jouables, key=lambda c: (scores[c], -points(c, atout)))

    def entame_experte(self, main, jouables, atout, connues, dehors, attaquant, moi, signaux):
        if attaquant and dehors:
            maitres = [c for c in jouables if c[1] == atout and self.est_maitre(c, atout, connues, main)]
            if maitres:
                return max(maitres, key=lambda c: force(c, atout, atout))
        maitres = [c for c in jouables if c[1] != atout and self.est_maitre(c, atout, connues, main)]
        if maitres:
            return max(maitres, key=lambda c: points(c, atout))
        partenaire = (moi + 2) % 4
        # Répondre à l'appel du partenaire : on rejoue la couleur par une petite carte.
        for couleur in sorted(signaux[partenaire]["appel"]):
            cartes = [c for c in jouables if c[1] == couleur and couleur != atout]
            if cartes:
                return min(cartes, key=lambda c: force(c, atout, c[1]))
        refus = signaux[partenaire]["refus"]
        appels_adverses = signaux[(moi + 1) % 4]["appel"] | signaux[(moi + 3) % 4]["appel"]
        pool = [c for c in jouables if c[1] != atout] or jouables
        preferees = [c for c in pool if c[1] not in refus and c[1] not in appels_adverses]
        return min(preferees or pool, key=lambda c: (points(c, atout), force(c, atout, c[1])))

    def suivre(self, main, jouables, pli, atout, connues, dehors, moi):
        demandee = pli[0][1][1]
        courant = gagnant_pli(pli, atout)
        meilleure = max(force(c, atout, demandee) for _, c in pli)
        dernier = len(pli) == 3
        enjeu = sum(points(c, atout) for _, c in pli)
        if courant == (moi + 2) % 4:
            carte_partenaire = next(c for j, c in pli if j == courant)
            sur = dernier or (
                self.est_maitre(carte_partenaire, atout, connues, main)
                and (carte_partenaire[1] == atout or not dehors)
            )
            if sur:
                return charge(jouables, atout, demandee)
            return self.defausse(main, jouables, atout, demandee, partenaire_gagne=True)
        gagnantes = [c for c in jouables if force(c, atout, demandee) > meilleure]
        if gagnantes:
            coupe = gagnantes[0][1] == atout and demandee != atout
            if not coupe or dernier or enjeu >= 10:
                return min(gagnantes, key=lambda c: force(c, atout, demandee))
        return self.defausse(main, jouables, atout, demandee, partenaire_gagne=False)

    def defausse(self, main, jouables, atout, demandee, partenaire_gagne):
        """Carte à donner quand on ne veut ou ne peut pas gagner le pli : c'est ici qu'on fait un appel."""
        hors = [c for c in jouables if c[1] not in (demandee, atout)]
        if not hors or any(c[1] == demandee for c in jouables):
            return min(jouables, key=lambda c: (points(c, atout), force(c, atout, c[1])))
        mes_as = {c[1] for c in main if c[0] == "As" and c[1] != atout}
        if partenaire_gagne:
            appels = [c for c in hors if c[1] in mes_as and c[0] in self.APPELS]
            if appels:
                return max(appels, key=lambda c: points(c, atout))
        poids = {couleur: sum(points(c, atout) for c in main if c[1] == couleur) for couleur in COULEURS}
        pool = [c for c in hors if c[1] not in mes_as] or hors
        return min(pool, key=lambda c: (points(c, atout), poids[c[1]], force(c, atout, c[1])))


class Humain:
    def debut_donne(self, moi, atout, preneur, contrat=None, mult=1):
        pass

    def _demander(self, texte):
        return input(texte).strip().lower()

    def prise(self, main, retournee, tour):
        print(f"\nVotre main : {afficher_main(main)}")
        if tour == 1:
            rep = self._demander(f"Carte retournée : {nom_carte(retournee)}. Prendre à {retournee[1]} ? (o/n) ")
            return retournee[1] if rep in ("o", "oui", "y") else None
        choix = [c for c in COULEURS if c != retournee[1]]
        while True:
            rep = self._demander(
                "Choisir un atout : " + ", ".join(f"{i + 1}={SYMBOLES[c]}" for i, c in enumerate(choix)) + " (n = passer) "
            )
            if rep in ("n", "non", ""):
                return None
            if rep.isdigit() and 1 <= int(rep) <= len(choix):
                return choix[int(rep) - 1]

    def enchere(self, main, courant, p):
        print(f"\nVotre main : {afficher_main(main)}")
        if courant is not None:
            print(f"Enchère actuelle : {nom_contrat(courant[0])} {SYMBOLES[courant[1]]} par {NOMS[courant[2]]}")
        valides = [v for v in ENCHERES if courant is None or v > courant[0]]
        while True:
            rep = self._demander(f"Valeur ({', '.join(nom_contrat(v) for v in valides)} ; p = passer) : ")
            if rep in ("p", "n", ""):
                return None
            valeur = CAPOT if rep == "capot" else int(rep) if rep.isdigit() else None
            if valeur in valides:
                break
        while True:
            rep = self._demander("Couleur : " + ", ".join(f"{i + 1}={SYMBOLES[c]}" for i, c in enumerate(COULEURS)) + " ")
            if rep.isdigit() and 1 <= int(rep) <= 4:
                return valeur, COULEURS[int(rep) - 1]

    def coinche(self, main, contrat):
        print(f"\nVotre main : {afficher_main(main)}")
        rep = self._demander(f"{NOMS[contrat[2]]} a pris {nom_contrat(contrat[0])} {SYMBOLES[contrat[1]]}. Coincher ? (o/n) ")
        return rep in ("o", "oui", "y")

    def surcoinche(self, main, contrat):
        rep = self._demander("Vous êtes coinchés. Surcoincher ? (o/n) ")
        return rep in ("o", "oui", "y")

    def choisir_carte(self, main, jouables, pli, atout, vus=()):
        if pli:
            print("Pli en cours : " + ", ".join(f"{NOMS[j]} {nom_carte(c)}" for j, c in pli))
        main = trier_main(main, atout)
        print("Votre main : " + "  ".join(
            f"[{i + 1}]{nom_carte(c)}" if c in jouables else f" -{nom_carte(c)}" for i, c in enumerate(main)
        ))
        while True:
            rep = self._demander("Votre carte (numéro) : ")
            if rep.isdigit() and 1 <= int(rep) <= len(main) and main[int(rep) - 1] in jouables:
                return main[int(rep) - 1]
            print("Carte non jouable.")


# --- Déroulement d'une donne ---------------------------------------------------

def encheres(joueurs, mains, retournee, donneur, parler):
    for tour in (1, 2):
        for k in range(4):
            p = apres(donneur, 1 + k)
            choix = joueurs[p].prise(mains[p], retournee, tour)
            if choix is not None:
                parler(f"{NOMS[p]} prend à {SYMBOLES[choix]} {choix}.")
                return p, choix
            parler(f"{NOMS[p]} passe.")
    return None, None


def encheres_coinche(joueurs, mains, donneur, parler):
    """Enchères de coinche. Renvoie (preneur, atout, valeur, multiplicateur) ou None."""
    courant = None
    passes = 0
    k = 0
    while True:
        p = apres(donneur, 1 + k)
        k += 1
        choix = joueurs[p].enchere(mains[p], courant, p)
        if choix is not None and (courant is None or choix[0] > courant[0]) and choix[0] in ENCHERES:
            courant = (choix[0], choix[1], p)
            passes = 0
            parler(f"{NOMS[p]} annonce {nom_contrat(choix[0])} {SYMBOLES[choix[1]]}.")
        else:
            passes += 1
            parler(f"{NOMS[p]} passe.")
        if courant is None and passes == 4:
            return None
        if courant is not None and passes == 3:
            break
    valeur, atout, preneur = courant
    mult = 1
    for adv in (apres(preneur, 1), apres(preneur, 3)):
        if joueurs[adv].coinche(mains[adv], courant):
            mult = 2
            parler(f"{NOMS[adv]} COINCHE !")
            if joueurs[preneur].surcoinche(mains[preneur], courant):
                mult = 4
                parler(f"{NOMS[preneur]} SURCOINCHE !")
            break
    return preneur, atout, valeur, mult


def jouer_donne(joueurs, donneur, parler=print, coinche=False):
    """Joue une donne. Renvoie None si personne ne prend, sinon un dict de résultats."""
    jeu = creer_jeu()
    random.shuffle(jeu)
    contrat, mult = None, 1

    if coinche:
        mains = [jeu[i * 8:(i + 1) * 8] for i in range(4)]
        parler(f"\n=== Donneur : {NOMS[donneur]} — coinche ===")
        res = encheres_coinche(joueurs, mains, donneur, parler)
        if res is None:
            parler("Personne n'enchérit : on redistribue.")
            return None
        preneur, atout, contrat, mult = res
        parler(f"Contrat : {nom_contrat(contrat)} {SYMBOLES[atout]} par {NOMS[preneur]}"
               + {1: "", 2: " (coinché x2)", 4: " (surcoinché x4)"}[mult])
    else:
        mains = [jeu[i * 5:(i + 1) * 5] for i in range(4)]
        retournee, reste = jeu[20], jeu[21:]
        parler(f"\n=== Donneur : {NOMS[donneur]} — carte retournée : {nom_carte(retournee)} ===")
        preneur, atout = encheres(joueurs, mains, retournee, donneur, parler)
        if preneur is None:
            parler("Personne ne prend : on redistribue.")
            return None
        mains[preneur].append(retournee)
        i = 0
        for p in range(4):
            n = 2 if p == preneur else 3
            mains[p] += reste[i:i + n]
            i += n
        parler(f"Atout : {SYMBOLES[atout]} {atout} (pris par {NOMS[preneur]})")

    belote_joueur = next((p for p in range(4)
                          if ("Roi", atout) in mains[p] and ("Dame", atout) in mains[p]), None)
    belote_equipe = None if belote_joueur is None else belote_joueur % 2

    for p, j in enumerate(joueurs):
        j.debut_donne(p, atout, preneur, contrat, mult)

    vus = []
    belote_jouees = 0
    cartes = [0, 0]
    plis = [0, 0]
    meneur = apres(donneur, 1)
    for numero in range(8):
        pli = []
        for k in range(4):
            p = apres(meneur, k)
            jouables = cartes_jouables(mains[p], pli, atout)
            carte = joueurs[p].choisir_carte(mains[p], jouables, pli, atout, vus)
            assert carte in jouables
            mains[p].remove(carte)
            pli.append((p, carte))
            if p != 0 or not isinstance(joueurs[0], Humain):
                parler(f"  {NOMS[p]} joue {nom_carte(carte)}")
            if p == belote_joueur and carte in (("Roi", atout), ("Dame", atout)):
                belote_jouees += 1
                parler("  ... Belote !" if belote_jouees == 1 else "  ... Rebelote !")
        gagnant = gagnant_pli(pli, atout)
        gain = sum(points(c, atout) for _, c in pli) + (BONUS_DIX_DE_DER if numero == 7 else 0)
        cartes[gagnant % 2] += gain
        plis[gagnant % 2] += 1
        parler(f"Pli {numero + 1} : {NOMS[gagnant]} (+{gain})")
        vus.extend(pli)
        meneur = gagnant

    return resultat(preneur, cartes, plis, belote_equipe, atout, contrat, mult)


def resultat(preneur, cartes, plis, belote_equipe, atout=None, contrat=None, mult=1):
    """Calcule les points d'une donne. contrat=None : belote contrat ; sinon coinche."""
    eq = preneur % 2
    totaux = list(cartes)
    if belote_equipe is not None:
        totaux[belote_equipe] += BONUS_BELOTE

    if contrat is None:
        for e in (0, 1):
            if plis[e] == 8:
                totaux[e] += BONUS_CAPOT
        rempli = totaux[eq] > totaux[1 - eq]
        marque = list(totaux)
        if not rempli:
            marque = [0, 0]
            marque[1 - eq] = TOTAL_CARTES
            if belote_equipe is not None:
                marque[belote_equipe] += BONUS_BELOTE
    else:
        rempli = plis[eq] == 8 if contrat == CAPOT else totaux[eq] >= contrat
        marque = [0, 0]
        if rempli:
            if mult == 1:
                marque[eq] = cartes[eq] + contrat
                marque[1 - eq] = cartes[1 - eq]
            else:
                marque[eq] = (TOTAL_CARTES + contrat) * mult
        else:
            marque[1 - eq] = (TOTAL_CARTES + contrat) * mult
        if belote_equipe is not None:
            marque[belote_equipe] += BONUS_BELOTE

    return {
        "preneur": preneur, "atout": atout, "contrat": contrat, "mult": mult,
        "cartes": cartes, "plis": plis, "belote": belote_equipe,
        "totaux": totaux, "marque": marque, "rempli": rempli,
    }


def jouer_partie(joueurs, cible=1000, parler=print, coinche=False):
    scores = [0, 0]
    donneur = random.randrange(4)
    while max(scores) < cible:
        res = jouer_donne(joueurs, donneur, parler, coinche)
        donneur = apres(donneur, 1)
        if res is None:
            continue
        for e in (0, 1):
            scores[e] += res["marque"][e]
        statut = "contrat rempli" if res["rempli"] else "CHUTE du preneur"
        parler(f"→ {statut} ; donne : {res['marque'][0]} - {res['marque'][1]} ; "
               f"total : {EQUIPES[0]} {scores[0]} / {EQUIPES[1]} {scores[1]}")
    if scores[0] != scores[1]:
        gagnante = 0 if scores[0] > scores[1] else 1
        parler(f"\nVictoire de l'équipe {EQUIPES[gagnante]} !")
    return scores


def main():
    parser = argparse.ArgumentParser(description="Belote")
    parser.add_argument("--coinche", action="store_true", help="mode coinche (enchères au point)")
    parser.add_argument("--bots", choices=["expert", "malin", "simple"], default="expert", help="niveau des bots")
    parser.add_argument("--auto", action="store_true", help="4 bots jouent entre eux")
    parser.add_argument("--seed", type=int, help="graine aléatoire")
    parser.add_argument("--cible", type=int, default=1000, help="score à atteindre (défaut 1000)")
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    bot = {"expert": BotExpert, "malin": BotMalin, "simple": Bot}[args.bots]
    joueurs = [bot() if args.auto else Humain(), bot(), bot(), bot()]
    jouer_partie(joueurs, args.cible, coinche=args.coinche)


if __name__ == "__main__":
    main()
