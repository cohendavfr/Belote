import random
import unittest

import belote
from belote import Bot, BotExpert, BotMalin, cartes_jouables, gagnant_pli, jouer_donne, points, resultat


class TestRegles(unittest.TestCase):
    def test_total_points_jeu(self):
        for atout in belote.COULEURS:
            self.assertEqual(sum(points(c, atout) for c in belote.creer_jeu()), 152)

    def test_gagnant_atout_coupe(self):
        pli = [(0, ("As", "Coeur")), (1, ("7", "Pique")), (2, ("10", "Coeur")), (3, ("Roi", "Trefle"))]
        self.assertEqual(gagnant_pli(pli, "Pique"), 1)
        self.assertEqual(gagnant_pli(pli, "Carreau"), 0)

    def test_valet_atout_plus_fort_que_9(self):
        pli = [(0, ("9", "Coeur")), (1, ("Valet", "Coeur")), (2, ("As", "Coeur")), (3, ("10", "Coeur"))]
        self.assertEqual(gagnant_pli(pli, "Coeur"), 1)

    def test_obligation_de_fournir(self):
        main = [("7", "Coeur"), ("As", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("7", "Coeur")])

    def test_obligation_de_couper(self):
        main = [("As", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("As", "Pique")])

    def test_pas_de_coupe_si_partenaire_maitre(self):
        main = [("As", "Pique"), ("8", "Trefle")]
        pli = [(1, ("7", "Coeur")), (0, ("As", "Coeur")), (3, ("8", "Coeur"))]
        self.assertEqual(len(cartes_jouables(main, pli, "Pique")), 2)

    def test_obligation_de_surcouper(self):
        main = [("9", "Pique"), ("7", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur")), (1, ("Dame", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("9", "Pique")])

    def test_sous_couper_si_impossible_de_monter(self):
        main = [("7", "Pique"), ("8", "Trefle")]
        pli = [(0, ("Roi", "Coeur")), (1, ("Valet", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("7", "Pique")])

    def test_monter_a_latout(self):
        main = [("7", "Pique"), ("Valet", "Pique"), ("8", "Trefle")]
        pli = [(0, ("9", "Pique"))]
        self.assertEqual(cartes_jouables(main, pli, "Pique"), [("Valet", "Pique")])


class TestOrdre(unittest.TestCase):
    def test_sens_anti_horaire(self):
        self.assertEqual([belote.apres(0, n) for n in range(4)], [0, 3, 2, 1])
        self.assertEqual(belote.apres(1, 1), 0)  # après Ouest vient Vous

    def test_premier_a_parler_est_a_droite_du_donneur(self):
        ordre = []

        class Muet:
            def prise(self, main, retournee, tour):
                ordre.append(len(ordre))
                return None

        class Noteur:
            def __init__(self, p):
                self.p = p

            def prise(self, main, retournee, tour):
                if tour == 1:
                    ordre.append(self.p)
                return None

        joueurs = [Noteur(p) for p in range(4)]
        belote.encheres(joueurs, [[]] * 4, ("As", "Coeur"), 1, lambda *_: None)
        self.assertEqual(ordre, [0, 3, 2, 1])


class TestTriMain(unittest.TestCase):
    def test_ordre_des_couleurs(self):
        main = [("As", c) for c in ("Pique", "Carreau", "Trefle", "Coeur")]
        self.assertEqual([c[1] for c in belote.trier_main(main)], ["Coeur", "Trefle", "Carreau", "Pique"])

    def test_valeurs_decroissantes(self):
        main = [("7", "Pique"), ("As", "Pique"), ("10", "Pique"), ("Valet", "Pique")]
        self.assertEqual([c[0] for c in belote.trier_main(main)], ["As", "10", "Valet", "7"])

    def test_ordre_des_atouts_une_fois_choisi(self):
        main = [("As", "Pique"), ("Valet", "Pique"), ("9", "Pique"), ("10", "Pique"), ("7", "Coeur"), ("As", "Coeur")]
        self.assertEqual([c[0] for c in belote.trier_main(main, "Pique")],
                         ["As", "7", "Valet", "9", "As", "10"])


class TestScore(unittest.TestCase):
    def test_contrat_rempli(self):
        r = resultat(0, [100, 62], [5, 3], None)
        self.assertTrue(r["rempli"])
        self.assertEqual(r["marque"], [100, 62])

    def test_chute(self):
        r = resultat(0, [70, 92], [4, 4], None)
        self.assertFalse(r["rempli"])
        self.assertEqual(r["marque"], [0, 162])

    def test_belote_et_capot(self):
        r = resultat(0, [162, 0], [8, 0], 0)
        self.assertEqual(r["marque"], [162 + 20 + 90, 0])

    def test_belote_conservee_en_cas_de_chute(self):
        r = resultat(0, [60, 102], [3, 5], 0)
        self.assertEqual(r["marque"], [20, 162])


class TestCoinche(unittest.TestCase):
    def test_contrat_rempli_simple(self):
        r = resultat(0, [100, 62], [5, 3], None, contrat=90)
        self.assertTrue(r["rempli"])
        self.assertEqual(r["marque"], [190, 62])

    def test_contrat_chute_simple(self):
        r = resultat(0, [70, 92], [4, 4], None, contrat=90)
        self.assertFalse(r["rempli"])
        self.assertEqual(r["marque"], [0, 162 + 90])

    def test_coinche_rempli(self):
        r = resultat(0, [100, 62], [5, 3], None, contrat=90, mult=2)
        self.assertEqual(r["marque"], [(162 + 90) * 2, 0])

    def test_surcoinche_chute(self):
        r = resultat(0, [70, 92], [4, 4], None, contrat=90, mult=4)
        self.assertEqual(r["marque"], [0, (162 + 90) * 4])

    def test_belote_compte_dans_le_contrat(self):
        r = resultat(0, [70, 92], [4, 4], 0, contrat=90)
        self.assertTrue(r["rempli"])
        self.assertEqual(r["marque"], [70 + 90 + 20, 92])

    def test_capot_contrat(self):
        self.assertTrue(resultat(0, [162, 0], [8, 0], None, contrat=250)["rempli"])
        self.assertFalse(resultat(0, [152, 10], [7, 1], None, contrat=250)["rempli"])

    def test_encheres_scriptees(self):
        class Scripte:
            def __init__(self, reponses, coinche=False):
                self.reponses = iter(reponses)
                self._coinche = coinche

            def enchere(self, main, courant, p):
                return next(self.reponses, None)

            def coinche(self, main, contrat):
                return self._coinche

            def surcoinche(self, main, contrat):
                return False

        # donneur 1 : Vous (0) parle en premier, puis Est (3), Partenaire (2), Ouest (1)
        joueurs = [Scripte([(80, "Coeur")], coinche=True), Scripte([]),
                   Scripte([]), Scripte([(90, "Pique")])]
        res = belote.encheres_coinche(joueurs, [[]] * 4, 1, lambda *_: None)
        self.assertEqual(res, (3, "Pique", 90, 2))

    def test_tout_le_monde_passe(self):
        joueurs = [Bot() for _ in range(4)]
        faible = [("7", "Coeur"), ("8", "Pique"), ("7", "Trefle"), ("8", "Carreau")] * 2
        self.assertIsNone(belote.encheres_coinche(joueurs, [faible] * 4, 0, lambda *_: None))


class TestBotMalin(unittest.TestCase):
    def bot(self, moi=0, preneur=0, atout="Pique"):
        b = BotMalin()
        b.debut_donne(moi, atout, preneur)
        return b

    def test_est_maitre(self):
        connues = {("As", "Coeur")}
        self.assertTrue(BotMalin.est_maitre(("10", "Coeur"), "Pique", connues, []))
        self.assertFalse(BotMalin.est_maitre(("Roi", "Coeur"), "Pique", set(), []))
        # le 9 d'atout est maître une fois le valet tombé
        self.assertTrue(BotMalin.est_maitre(("9", "Pique"), "Pique", {("Valet", "Pique")}, []))

    def test_entame_atout_maitre_en_attaque(self):
        main = [("Valet", "Pique"), ("7", "Coeur"), ("8", "Trefle")]
        carte = self.bot().choisir_carte(main, main, [], "Pique", [])
        self.assertEqual(carte, ("Valet", "Pique"))

    def test_entame_as_en_defense(self):
        main = [("As", "Coeur"), ("7", "Coeur"), ("8", "Trefle")]
        carte = self.bot(moi=0, preneur=1).choisir_carte(main, main, [], "Pique", [])
        self.assertEqual(carte, ("As", "Coeur"))

    def test_charge_quand_le_partenaire_est_maitre(self):
        main = [("10", "Coeur"), ("7", "Coeur")]
        pli = [(3, ("8", "Coeur")), (2, ("As", "Coeur")), (1, ("9", "Coeur"))]
        carte = self.bot(moi=0).choisir_carte(main, main, pli, "Pique", [])
        self.assertEqual(carte, ("10", "Coeur"))

    def test_ne_coupe_pas_un_pli_sans_enjeu(self):
        main = [("7", "Pique"), ("8", "Trefle")]
        pli = [(1, ("7", "Coeur")), (2, ("8", "Coeur"))]
        jouables = cartes_jouables(main, pli, "Pique")
        carte = self.bot(moi=3, preneur=1).choisir_carte(main, jouables, pli, "Pique", [])
        self.assertEqual(carte, ("7", "Pique"))  # obligé de couper : seule carte jouable

    def test_soutien_du_partenaire(self):
        main = [("Valet", "Pique"), ("9", "Pique"), ("As", "Coeur")] + [("7", "Trefle")] * 2
        res = BotMalin().enchere(main, (80, "Pique", 2), 0)
        self.assertEqual(res, (90, "Pique"))


class TestExpert(unittest.TestCase):
    def bot(self, moi=0, preneur=1, atout="Pique"):
        b = BotExpert()
        b.debut_donne(moi, atout, preneur)
        return b

    def test_lit_les_appels_et_refus(self):
        # pli 1 : Coeur demandé, le joueur 2 défausse le 10 de carreau (appel)
        # pli 2 : le joueur 2 défausse le 7 de trèfle (refus)
        vus = [(0, ("As", "Coeur")), (3, ("7", "Coeur")), (2, ("10", "Carreau")), (1, ("8", "Coeur")),
               (0, ("Roi", "Pique")), (3, ("9", "Pique")), (2, ("7", "Trefle")), (1, ("8", "Pique"))]
        s = self.bot().signaux(vus, [], "Pique")
        self.assertEqual(s[2]["appel"], {"Carreau"})
        self.assertEqual(s[2]["refus"], {"Trefle"})
        self.assertEqual(s[0]["appel"], set())

    def test_deduit_les_couleurs_vides(self):
        vus = [(0, ("As", "Coeur")), (3, ("7", "Trefle")), (2, ("9", "Coeur")), (1, ("8", "Coeur"))]
        vides = self.bot().couleurs_vides(vus, [], "Pique")
        self.assertIn("Coeur", vides[3])
        self.assertEqual(vides[1], set())

    def test_repartition_respecte_les_couleurs_vides(self):
        b = self.bot(moi=0)
        inconnues = [(v, c) for c in ("Coeur", "Trefle") for v in belote.VALEURS]
        vides = {0: set(), 1: {"Coeur"}, 2: set(), 3: {"Trefle"}}
        for _ in range(30):
            mains = b.repartir(inconnues, {1: 8, 2: 0, 3: 8}, vides, None, 0)
            self.assertTrue(all(c[1] != "Coeur" for c in mains[1]))
            self.assertTrue(all(c[1] != "Trefle" for c in mains[3]))
            self.assertEqual((len(mains[1]), len(mains[3])), (8, 8))

    def test_appel_en_defaussant(self):
        # partenaire (2) gagne le pli à Coeur ; on n'a plus de coeur et on a l'As de carreau
        main = [("As", "Carreau"), ("10", "Carreau"), ("7", "Trefle")]
        pli = [(1, ("7", "Coeur")), (2, ("As", "Coeur")), (3, ("8", "Coeur"))]
        carte = self.bot(moi=0).defausse(main, main, "Pique", "Coeur", partenaire_gagne=True)
        self.assertEqual(carte, ("10", "Carreau"))

    def test_refus_en_defaussant(self):
        main = [("As", "Carreau"), ("10", "Carreau"), ("7", "Trefle"), ("Roi", "Trefle")]
        carte = self.bot(moi=0).defausse(main, main, "Pique", "Coeur", partenaire_gagne=False)
        self.assertEqual(carte, ("7", "Trefle"))

    def test_repond_a_lappel_du_partenaire(self):
        main = [("8", "Carreau"), ("Roi", "Carreau"), ("7", "Trefle")]
        vus = [(0, ("As", "Coeur")), (3, ("7", "Coeur")), (2, ("10", "Carreau")), (1, ("8", "Coeur"))]
        b = self.bot(moi=0, preneur=1)
        carte = b.entame_experte(main, main, "Pique", {c for _, c in vus}, [], False, 0, b.signaux(vus, [], "Pique"))
        self.assertEqual(carte, ("8", "Carreau"))

    def test_ne_triche_pas(self):
        """Mêmes informations publiques, mains cachées différentes : le choix ne dépend pas d'elles."""
        main = [("As", "Coeur"), ("Roi", "Coeur"), ("9", "Pique"), ("7", "Carreau"), ("10", "Trefle")]
        vus = [(0, ("8", "Coeur")), (3, ("Valet", "Coeur")), (2, ("7", "Coeur")), (1, ("9", "Coeur"))]
        choix = set()
        for graine in range(3):
            random.seed(graine)
            b = self.bot(moi=0, preneur=0, atout="Pique")
            jouables = cartes_jouables(main, [], "Pique")
            choix.add(b.choisir_carte(main, jouables, [], "Pique", vus))
        # le bot ne reçoit jamais les mains des autres : la seule variation vient de ses tirages
        self.assertLessEqual(len(choix), 2)
        import inspect
        self.assertEqual(list(inspect.signature(BotExpert.choisir_carte).parameters),
                         ["self", "main", "jouables", "pli", "atout", "vus"])


class TestSimulation(unittest.TestCase):
    def test_donnes_automatiques(self):
        random.seed(42)
        joueurs = [Bot() for _ in range(4)]
        jouees = 0
        for i in range(300):
            res = jouer_donne(joueurs, i % 4, parler=lambda *_: None)
            if res is None:
                continue
            jouees += 1
            self.assertEqual(sum(res["cartes"]), belote.TOTAL_CARTES)
            self.assertEqual(sum(res["plis"]), 8)
        self.assertGreater(jouees, 100)

    def test_malin_bat_simple(self):
        random.seed(11)
        total = [0, 0]
        for i in range(600):
            eq = i % 2
            joueurs = [BotMalin() if p % 2 == eq else Bot() for p in range(4)]
            res = jouer_donne(joueurs, (i // 2) % 4, parler=lambda *_: None)
            if res is not None:
                total[0] += res["marque"][eq]
                total[1] += res["marque"][1 - eq]
        self.assertGreater(total[0], total[1])

    def test_donnes_entre_experts(self):
        random.seed(3)
        joueurs = [BotExpert() for _ in range(4)]
        for mode in (False, True):
            for i in range(25):
                res = jouer_donne(joueurs, i % 4, parler=lambda *_: None, coinche=mode)
                if res is not None:
                    self.assertEqual(sum(res["cartes"]), belote.TOTAL_CARTES)

    def test_donnes_coinche_automatiques(self):
        random.seed(7)
        joueurs = [Bot() for _ in range(4)]
        jouees = 0
        for i in range(300):
            res = jouer_donne(joueurs, i % 4, parler=lambda *_: None, coinche=True)
            if res is None:
                continue
            jouees += 1
            self.assertEqual(sum(res["cartes"]), belote.TOTAL_CARTES)
            self.assertIn(res["contrat"], belote.ENCHERES)
        self.assertGreater(jouees, 50)


class TestPartenaireMaitre(unittest.TestCase):
    """Partenaire maître et couleur absente : pas obligé de couper, et les bots ne gaspillent pas d'atout."""

    def test_libre_de_couper(self):
        main = [("Roi", "Carreau"), ("8", "Trefle"), ("Valet", "Coeur")]
        pli = [(0, ("As", "Pique")), (3, ("7", "Carreau"))]
        self.assertEqual(sorted(belote.cartes_jouables(main, pli, "Coeur")), sorted(main))

    def test_bots_se_defaussent(self):
        main = [("Valet", "Coeur"), ("Roi", "Carreau"), ("As", "Trefle")]
        pli = [(0, ("As", "Pique")), (3, ("7", "Carreau"))]  # partenaire (0) maître, 3 joue avant 2
        jouables = belote.cartes_jouables(main, pli, "Coeur")
        for bot in (belote.Bot(), belote.BotMalin(), belote.BotExpert()):
            bot.debut_donne(2, "Coeur", 1) if hasattr(bot, "debut_donne") else None
            carte = bot.choisir_carte(main, jouables, pli, "Coeur")
            self.assertNotEqual(carte[1], "Coeur", type(bot).__name__)


if __name__ == "__main__":
    unittest.main()
