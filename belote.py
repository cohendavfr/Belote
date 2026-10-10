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

    joueur = (pli[0][0] + len(pli)) % 4
    if gagnant_pli(pli, atout) == (joueur + 2) % 4:
        return list(main)

    atouts = [c for c in main if c[1] == atout]
    if atouts:
        plus_forts = [c for c in atouts if force(c, atout, demandee) > meilleure]
        return plus_forts or atouts
    return list(main)


def trier_main(main, atout=None):
    def cle(c):
        ordre = ORDRE_ATOUT if c[1] == atout else ORDRE_PLAIN
        return (c[1] == atout, COULEURS.index(c[1]), ordre.index(c[0]))
    return sorted(main, key=cle)


def afficher_main(main, atout=None):
    return "  ".join(nom_carte(c) for c in trier_main(main, atout))


# --- Joueurs -----------------------------------------------------------------

class Bot:
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
            seuil = 45
        else:
            candidats = [c for c in COULEURS if c != retournee[1]]
            seuil = 42
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

    def choisir_carte(self, main, jouables, pli, atout):
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
        joueur = (pli[0][0] + len(pli)) % 4
        if courant == (joueur + 2) % 4:
            return max(jouables, key=lambda c: points(c, atout))
        meilleure = max(force(c, atout, demandee) for _, c in pli)
        gagnantes = [c for c in jouables if force(c, atout, demandee) > meilleure]
        if gagnantes:
            return min(gagnantes, key=lambda c: force(c, atout, demandee))
        return min(jouables, key=lambda c: (points(c, atout), force(c, atout, demandee)))


class Humain:
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

    def choisir_carte(self, main, jouables, pli, atout):
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
            p = (donneur + 1 + k) % 4
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
        p = (donneur + 1 + k) % 4
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
    for adv in ((preneur + 1) % 4, (preneur + 3) % 4):
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

    belote_jouees = 0
    cartes = [0, 0]
    plis = [0, 0]
    meneur = (donneur + 1) % 4
    for numero in range(8):
        pli = []
        for k in range(4):
            p = (meneur + k) % 4
            jouables = cartes_jouables(mains[p], pli, atout)
            carte = joueurs[p].choisir_carte(mains[p], jouables, pli, atout)
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
        donneur = (donneur + 1) % 4
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
    parser.add_argument("--auto", action="store_true", help="4 bots jouent entre eux")
    parser.add_argument("--seed", type=int, help="graine aléatoire")
    parser.add_argument("--cible", type=int, default=1000, help="score à atteindre (défaut 1000)")
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    joueurs = [Bot() if args.auto else Humain(), Bot(), Bot(), Bot()]
    jouer_partie(joueurs, args.cible, coinche=args.coinche)


if __name__ == "__main__":
    main()
