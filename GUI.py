import sys
import os
import types
import threading
import builtins
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QLabel, QPushButton, QFileDialog, QDialog, QScrollArea,QGroupBox, QFormLayout, QCheckBox, QLineEdit, QFrame,QMessageBox, QProgressBar, QDesktopWidget, QTextEdit, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE D'INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

SPLASH_STYLE = """QProgressBar#barre {background-color: #E0E0E0;border: none;border-radius: 4px;} QProgressBar#barre::chunk {background-color: #2196F3;border-radius: 4px;}"""

application = QApplication(sys.argv)
application.setStyleSheet(SPLASH_STYLE)

splash = QWidget()
splash.setObjectName("splash")
splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
splash.resize(420, 160)

geo = QDesktopWidget().availableGeometry()
splash.move(geo.center().x() - 210, geo.center().y() - 80)

layout_splash = QVBoxLayout(splash)
layout_splash.setContentsMargins(40, 36, 40, 30)
layout_splash.setSpacing(8)

lbl_titre = QLabel("imsCORE")
lbl_titre.setStyleSheet("font-size: 22px; font-weight: bold;")
lbl_titre.setAlignment(Qt.AlignCenter)

lbl_etape = QLabel()
lbl_etape.setObjectName("etape")
lbl_etape.setStyleSheet("color: #4A90D9; font-size: 11px;")
lbl_etape.setAlignment(Qt.AlignCenter)

barre = QProgressBar()
barre.setObjectName("barre")
barre.setRange(0, 0)
barre.setTextVisible(False)
barre.setFixedHeight(6)

layout_splash.addWidget(lbl_titre)
layout_splash.addStretch()
layout_splash.addWidget(lbl_etape)
layout_splash.addWidget(barre)

splash.show()
application.processEvents()

etat = {"message": "", "termine": False}

def charger_modules():
    etat["message"] = "Loading app ..."
    import imsCORE_pipeline as pipeline
    builtins._pipeline_module = pipeline
    etat["termine"] = True

threading.Thread(target=charger_modules, daemon=True).start()

def verifier_chargement():
    lbl_etape.setText(etat["message"])
    if etat["termine"]:
        timer_splash.stop()
        barre.setRange(0, 100)
        barre.setValue(100)
        global pipeline
        pipeline = builtins._pipeline_module
        splash.close()
        fenetre_choix.show()

timer_splash = QTimer()
timer_splash.setInterval(100)
timer_splash.timeout.connect(verifier_chargement)
timer_splash.start()

# ══════════════════════════════════════════════════════════════════════════════
# TEXTES D'AIDE
# ══════════════════════════════════════════════════════════════════════════════

AIDE = {
    "MZ_MIN":                "Minimum Masse range",
    "MZ_MAX":                "Maximum Masse range",
    "MZ_BIN_SIZE":           "Binary size of the mass range",
    "NORMALIZE_TIC":         "If the checkbox is checked, apply the TIC normalization algorithm",
    "AUTO_TISSUE_MASK":      "If the checkbox is checked, apply the tissue mask",
    "TIC_TISSUE_QUANTILE":   "Precision of the tissue mask",
    "N_PCA_COMPONENTS":      "Number of PCA components to retain",
    "MAX_CLUSTERS":          "Maximum number of clusters",
    "SILHOUETTE_THRESHOLD":  "The minimum silhouette score a cluster must achieve to be included in the data to be analyzed",
    "MIN_CLUSTER_SIZE":      "Minimum cluster size",
    "N_INIT_KMEANS":         "Number of runs of the k-means algorithm with different initial values for the centroids",
    "RANDOM_STATE":          "During clustering, if the value is not 0, the data changes slightly each time the program runs.",
    "UMAP_N_NEIGHBORS":      "Number of neighbors of a point",
    "UMAP_MIN_DIST":         "Minimum distance between two points in the UMAP",
    "UMAP_N_COMPONENTS":     "Number of components in the UMAP",
    "CSV_PIXELS":            "Name of the CSV file that will contain all the information about the pixels",
    "CSV_SPECTRA":           "Name of the CSV file that will contain all the information about the spectra",
    "CSV_PEAKS":             "Name of the CSV file that will contain all the information about the peaks",
    "CSV_LABEL_RATIOS":      "Name of the CSV file that will contain the label ratios",
    "max_intensity_size":    "Maximum number of intensity values per spectrum used in the PKL model prediction",
}

# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE PARAMÈTRES PERSONNALISÉS
# ══════════════════════════════════════════════════════════════════════════════

def fenetre_params_perso_pkl(fenetre_parent):
    """Fenêtre de paramètres personnalisés pour l'analyse PKL (MZ_MIN, MZ_MAX, max_intensity_size)"""
    dialogue = QDialog(fenetre_parent)
    dialogue.setWindowTitle("Custom Settings")
    dialogue.resize(560, 280)

    disposition_externe = QVBoxLayout(dialogue)
    disposition_externe.setContentsMargins(0, 0, 0, 0)

    contenu = QWidget()
    disposition_formulaire = QVBoxLayout(contenu)
    disposition_formulaire.setContentsMargins(30, 24, 30, 24)
    disposition_formulaire.setSpacing(14)

    tous_les_champs = []

    def afficher_aide(attr, fenetre_ref):
        QMessageBox.information(fenetre_ref, f"Aide - {attr}", AIDE.get(attr, " "))

    groupe = QGroupBox("📊  PKL Analysis Parameters")
    groupe.setStyleSheet("""QGroupBox {font-weight: bold; font-size: 13px;border: 1px solid #ddd; border-radius: 8px;margin-top: 8px; padding: 10px;} QGroupBox::title {subcontrol-origin: margin; left: 12px;padding: 0 6px; color: #4A90D9;}""")
    disposition_champs = QFormLayout(groupe)
    disposition_champs.setSpacing(8)

    for etiquette, attr, type_ in [
        ("Minimum m/z range", "MZ_MIN", float),
        ("Maximum m/z range", "MZ_MAX", float),
        ("Max intensity size", "max_intensity_size", int),
        ("Label ratios file", "CSV_LABEL_RATIOS", str),
        ("Tissue mask quantile", "TIC_TISSUE_QUANTILE", float),
    ]:
        conteneur = QWidget()
        ligne = QHBoxLayout(conteneur)
        ligne.setContentsMargins(0, 0, 0, 0)
        ligne.setSpacing(6)
        widget = QLineEdit("")
        widget.setPlaceholderText(str(getattr(pipeline, attr)))
        widget.setFixedHeight(30)
        widget.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 0 6px;")
        bouton_aide = QPushButton("❓")
        bouton_aide.setFixedSize(24, 24)
        bouton_aide.setStyleSheet("""QPushButton {font-size: 12px; font-weight: bold;background-color: #BDC3C7; color: white;border-radius: 12px; border: none;} QPushButton:hover { background-color: #95A5A6; }""")
        bouton_aide.clicked.connect(lambda _, a=attr, f=dialogue: afficher_aide(a, f))
        ligne.addWidget(widget)
        ligne.addWidget(bouton_aide)
        tous_les_champs.append((attr, type_, widget))
        disposition_champs.addRow(etiquette, conteneur)

    disposition_formulaire.addWidget(groupe)
    disposition_externe.addWidget(contenu)

    separateur = QFrame()
    separateur.setFrameShape(QFrame.HLine)
    separateur.setStyleSheet("color: #ddd;")
    disposition_externe.addWidget(separateur)

    bouton_confirmer = QPushButton("💾  Confirm settings")
    bouton_confirmer.setFixedHeight(45)
    bouton_confirmer.setStyleSheet("""QPushButton { font-size: 13px; background-color: #27AE60; color: white; border-radius: 8px; margin: 10px 30px; } QPushButton:hover { background-color: #1E8449; }""")

    def confirmer_params_pkl():
        erreurs = []
        parametres_modifies = []
        for attr, type_, widget in tous_les_champs:
            try:
                if widget.text().strip() == "":
                    parametres_modifies.append(f"{attr} = {getattr(pipeline, attr)} (Unchanged)")
                else:
                    nouvelle_valeur = type_(widget.text().strip())
                    setattr(pipeline, attr, nouvelle_valeur)
                    parametres_modifies.append(f"{attr} = {nouvelle_valeur}")
            except ValueError:
                erreurs.append(attr)
        if erreurs:
            QMessageBox.warning(dialogue, "Error", "Invalid values :\n" + "\n".join(erreurs))
        else:
            resume = "\n".join(parametres_modifies)
            QMessageBox.information(dialogue, "Settings confirmed", f"✅ Settings confirmed :\n\n{resume}")
            dialogue.close()
            fenetre_parent.close()
            lancer_pipeline()

    bouton_confirmer.clicked.connect(confirmer_params_pkl)
    disposition_externe.addWidget(bouton_confirmer)

    dialogue.exec_()


def fenetre_params_perso(fenetre_parent):
    """Gestion de la fenetre des paramètres personnalisés"""
    if chemin_pkl_selectionne:
        fenetre_params_perso_pkl(fenetre_parent)
        return

    dialogue = QDialog(fenetre_parent)
    dialogue.setWindowTitle("Custom Settings")
    dialogue.resize(560, 650)

    disposition_externe = QVBoxLayout(dialogue)
    disposition_externe.setContentsMargins(0, 0, 0, 0)

    defilement = QScrollArea()
    defilement.setWidgetResizable(True)
    defilement.setStyleSheet("border: none;")

    contenu = QWidget()
    disposition_formulaire = QVBoxLayout(contenu)
    disposition_formulaire.setContentsMargins(30, 24, 30, 24)
    disposition_formulaire.setSpacing(14)

    tous_les_champs = []

    def afficher_aide(attr, fenetre_ref):
        QMessageBox.information(fenetre_ref, f"Aide - {attr}", AIDE.get(attr, " "))

    def creer_ligne_champ(attr, type_, fenetre_ref):
        conteneur = QWidget()
        ligne = QHBoxLayout(conteneur)
        ligne.setContentsMargins(0, 0, 0, 0)
        ligne.setSpacing(6)

        if type_ == bool:
            widget = QCheckBox()
            widget.setChecked(bool(getattr(pipeline, attr)))
        else:
            widget = QLineEdit("")
            widget.setPlaceholderText(str(getattr(pipeline, attr)))
            widget.setFixedHeight(30)
            widget.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 0 6px;")

        bouton_aide = QPushButton("❓")
        bouton_aide.setFixedSize(24, 24)
        bouton_aide.setStyleSheet("""QPushButton {font-size: 12px; font-weight: bold;background-color: #BDC3C7; color: white;border-radius: 12px; border: none;} QPushButton:hover { background-color: #95A5A6; }""")
        bouton_aide.clicked.connect(lambda _, a=attr, f=fenetre_ref: afficher_aide(a, f))

        ligne.addWidget(widget)
        ligne.addWidget(bouton_aide)

        tous_les_champs.append((attr, type_, widget))
        return conteneur

    def creer_groupe(titre, champs):
        groupe = QGroupBox(titre)
        groupe.setStyleSheet("""QGroupBox {font-weight: bold; font-size: 13px;border: 1px solid #ddd; border-radius: 8px;margin-top: 8px; padding: 10px;} QGroupBox::title {subcontrol-origin: margin; left: 12px;padding: 0 6px; color: #4A90D9;}""")
        disposition_champs = QFormLayout(groupe)
        disposition_champs.setSpacing(8)
        for etiquette, attr, type_ in champs:
            ligne_champ = creer_ligne_champ(attr, type_, dialogue)
            disposition_champs.addRow(etiquette, ligne_champ)
        return groupe

    disposition_formulaire.addWidget(creer_groupe("📊  m/z range", [("Minimum Masse range", "MZ_MIN", float), ("Maximum Masse range", "MZ_MAX", float), ("MZ_BIN_SIZE", "MZ_BIN_SIZE", float),]))
    disposition_formulaire.addWidget(creer_groupe("🔧  Normalization & Filtering", [("TIC Normalization", "NORMALIZE_TIC", bool),]))
    disposition_formulaire.addWidget(creer_groupe("🩺  Tissue mask", [("Auto mask", "AUTO_TISSUE_MASK", bool), ("Quantile TIC tissu", "TIC_TISSUE_QUANTILE", float),]))
    disposition_formulaire.addWidget(creer_groupe("📐  PCA", [("Number of components", "N_PCA_COMPONENTS", int),]))
    disposition_formulaire.addWidget(creer_groupe("🧮  Bisecting K-Means", [("Max Clusters ", "MAX_CLUSTERS", int), ("Silhouette Threshold", "SILHOUETTE_THRESHOLD", float), ("Min cluster size", "MIN_CLUSTER_SIZE", int), ("KMeans Initialisations", "N_INIT_KMEANS", int), ("Random state", "RANDOM_STATE", int),]))
    disposition_formulaire.addWidget(creer_groupe("🗺️  UMAP", [("Number of neighbors", "UMAP_N_NEIGHBORS", int), ("Minimum distance", "UMAP_MIN_DIST", float), ("UMAP Component", "UMAP_N_COMPONENTS", int),]))
    disposition_formulaire.addWidget(creer_groupe("💾  CSV Exports", [("Pixels file", "CSV_PIXELS", str), ("Spectres file", "CSV_SPECTRA", str), ("Peaks file", "CSV_PEAKS", str),]))

    defilement.setWidget(contenu)
    disposition_externe.addWidget(defilement)

    separateur = QFrame()
    separateur.setFrameShape(QFrame.HLine)
    separateur.setStyleSheet("color: #ddd;")
    disposition_externe.addWidget(separateur)

    bouton_confirmer = QPushButton("💾  Confirm settings")
    bouton_confirmer.setFixedHeight(45)
    bouton_confirmer.setStyleSheet("""QPushButton { font-size: 13px; background-color: #27AE60; color: white; border-radius: 8px; margin: 10px 30px; } QPushButton:hover { background-color: #1E8449; }""")

    def confirmer_params():
        erreurs = []
        parametres_modifies = []
        for attr, type_, widget in tous_les_champs:
            try:
                if type_ == bool:
                    nouvelle_valeur = widget.isChecked()
                    setattr(pipeline, attr, nouvelle_valeur)
                    parametres_modifies.append(f"{attr} = {nouvelle_valeur}")
                elif widget.text().strip() == "":
                    parametres_modifies.append(f"{attr} = {getattr(pipeline, attr)} (Unchanged)")
                else:
                    nouvelle_valeur = type_(widget.text().strip())
                    setattr(pipeline, attr, nouvelle_valeur)
                    parametres_modifies.append(f"{attr} = {nouvelle_valeur}")
            except ValueError:
                erreurs.append(attr)

        if erreurs:
            QMessageBox.warning(dialogue, "Error", "Invalid values :\n" + "\n".join(erreurs))
        else:
            resume = "\n".join(parametres_modifies)
            QMessageBox.information(dialogue, "Settings confirmed", f"✅ Settings confirmed :\n\n{resume}")
            dialogue.close()
            fenetre_parent.close()
            lancer_pipeline()

    bouton_confirmer.clicked.connect(confirmer_params)
    disposition_externe.addWidget(bouton_confirmer)

    dialogue.exec_()

# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE TIC MAP / MASQUE TISSU
# ══════════════════════════════════════════════════════════════════════════════

def ouvrir_fenetre_resultats(fig, logs):
    fenetre_res = QMainWindow()
    fenetre_res.setWindowTitle("imsCORE - TIC Map / Tissue Mask")
    fenetre_res.resize(1100, 700)

    geo = QDesktopWidget().availableGeometry()
    fenetre_res.move(geo.center().x() - 550, geo.center().y() - 350)

    w = QWidget()
    fenetre_res.setCentralWidget(w)
    layout_res = QVBoxLayout(w)
    layout_res.setContentsMargins(10, 10, 10, 10)
    layout_res.setSpacing(6)

    # barre d'outils + canvas matplotlib
    canvas  = FigureCanvasQTAgg(fig)
    toolbar = NavigationToolbar2QT(canvas, fenetre_res)
    layout_res.addWidget(toolbar)
    layout_res.addWidget(canvas)

    # zone de logs en bas
    log_zone = QTextEdit()
    log_zone.setReadOnly(True)
    log_zone.setFixedHeight(100)
    log_zone.setStyleSheet("font-family: monospace; font-size: 11px; background: #1e1e1e; color: #ccc; border-radius: 4px;")
    log_zone.setPlainText("\n".join(logs))  
    layout_res.addWidget(log_zone)

    bouton_suite = QPushButton("▶  Next - PCA Analysis " if not pipeline.chemin_pkl else "▶  Next - Label Maps")
    bouton_suite.setFixedHeight(42)
    bouton_suite.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white;border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def suite_clicked():
        fenetre_res.close()
        if pipeline.chemin_pkl:
            lancer_label_maps()
        else:
            lancer_pca()

    bouton_suite.clicked.connect(suite_clicked)
    layout_res.addWidget(bouton_suite)

    builtins._fenetre_res = fenetre_res
    fenetre_res.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE PCA
# ══════════════════════════════════════════════════════════════════════════════

def lancer_pca():
    """Lance run_PCA() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading PCA")
    fenetre_load.resize(420, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 210, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading PCA, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_pca = fenetre_load

    etat_pca = {"fig": None, "termine": False, "logs": []}

    # Rediriger stdout pour capturer les prints de run_PCA
    sys.stdout = types.SimpleNamespace(write=lambda txt: etat_pca["logs"].append(txt.rstrip()) if txt.strip() else None,flush=lambda: None )

    def run_pca():
        etat_pca["fig"] = pipeline.run_PCA()
        etat_pca["termine"] = True

    threading.Thread(target=run_pca, daemon=True).start()

    timer_pca = QTimer()
    timer_pca.setInterval(200)
    builtins._timer_pca = timer_pca

    def verifier_pca():
        if etat_pca["termine"]:
            timer_pca.stop()
            sys.stdout = sys.__stdout__
            fenetre_load.close()
            ouvrir_fenetre_pca(etat_pca["fig"], etat_pca["logs"])

    timer_pca.timeout.connect(verifier_pca)
    timer_pca.start()


def ouvrir_fenetre_pca(fig, logs):
    """Affiche le graphique PCA + logs dans une nouvelle fenêtre."""
    fenetre_pca = QMainWindow()
    fenetre_pca.setWindowTitle("imsCORE - Variance Explained by PCA")
    fenetre_pca.resize(950, 600)

    geo = QDesktopWidget().availableGeometry()
    fenetre_pca.move(geo.center().x() - 475, geo.center().y() - 300)

    w = QWidget()
    fenetre_pca.setCentralWidget(w)
    layout_pca = QVBoxLayout(w)
    layout_pca.setContentsMargins(10, 10, 10, 10)
    layout_pca.setSpacing(6)

    canvas  = FigureCanvasQTAgg(fig)
    toolbar = NavigationToolbar2QT(canvas, fenetre_pca)
    layout_pca.addWidget(toolbar)
    layout_pca.addWidget(canvas)

    log_zone = QTextEdit()
    log_zone.setReadOnly(True)
    log_zone.setFixedHeight(100)
    log_zone.setStyleSheet("font-family: monospace; font-size: 11px; ""background: #1e1e1e; color: #ccc; border-radius: 4px;")
    log_zone.setPlainText("\n".join(logs))
    layout_pca.addWidget(log_zone)

    # bouton "Suite → Bisecting KMeans"
    bouton_suite_bkm = QPushButton("▶  Next - Bisecting K-Means")
    bouton_suite_bkm.setFixedHeight(42)
    bouton_suite_bkm.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white;border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def suite_bkm_clicked():
        fenetre_pca.close()
        lancer_bkm()

    bouton_suite_bkm.clicked.connect(suite_bkm_clicked)
    layout_pca.addWidget(bouton_suite_bkm)

    builtins._fenetre_pca = fenetre_pca
    fenetre_pca.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE BISECTING K-MEANS ARBRE RECURSIF
# ══════════════════════════════════════════════════════════════════════════════

def lancer_bkm():
    """Lance run_bissceting_kmeans_tree() en arrière-plan avec une fenêtre de chargement."""

    # ── Fenêtre de chargement ─────────────────────────────────────────────────
    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Bissecting")
    fenetre_load.resize(440, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 220, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Bissecting K-Means Loading, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_bkm = fenetre_load

    etat_bkm = {"logs": [], "termine": False, "fig": None}

    # Capturer les prints ligne par ligne
    sys.stdout = types.SimpleNamespace(write=lambda txt: etat_bkm["logs"].append(txt.rstrip()) if txt.strip() else None,flush=lambda: None)

    def run_bkm():
        try:
            etat_bkm["fig"] = pipeline.run_bissceting_kmeans_tree()
        finally:
            etat_bkm["termine"] = True

    threading.Thread(target=run_bkm, daemon=True).start()

    timer_bkm = QTimer()
    timer_bkm.setInterval(200)
    builtins._timer_bkm = timer_bkm

    def verifier_bkm():
        # Mise à jour live des logs si la fenêtre résultats est déjà ouverte
        if hasattr(builtins, '_fenetre_bkm') and builtins._fenetre_bkm is not None:
            if hasattr(builtins, '_log_zone_bkm'):
                builtins._log_zone_bkm.setPlainText("\n".join(etat_bkm["logs"]))
                sb = builtins._log_zone_bkm.verticalScrollBar()
                sb.setValue(sb.maximum())

        if etat_bkm["termine"]:
            timer_bkm.stop()
            sys.stdout = sys.__stdout__
            fenetre_load.close()
            ouvrir_fenetre_bkm(etat_bkm["logs"], etat_bkm["fig"])

    timer_bkm.timeout.connect(verifier_bkm)
    timer_bkm.start()


def ouvrir_fenetre_bkm(logs, fig):
    """Affiche les logs Bisecting K-Means dans une nouvelle fenêtre."""
    fenetre_bkm = QMainWindow()
    fenetre_bkm.setWindowTitle("imsCORE - Bissecting K-Means ,  recursive tree with local Silhouette")
    fenetre_bkm.resize(1100, 800)

    geo = QDesktopWidget().availableGeometry()
    fenetre_bkm.move(geo.center().x() - 550, geo.center().y() - 400)

    w = QWidget()
    fenetre_bkm.setCentralWidget(w)
    layout_bkm = QVBoxLayout(w)
    layout_bkm.setContentsMargins(14, 14, 14, 14)
    layout_bkm.setSpacing(8)

    if fig is not None:
        canvas  = FigureCanvasQTAgg(fig)
        toolbar = NavigationToolbar2QT(canvas, fenetre_bkm)
        layout_bkm.addWidget(toolbar)
        layout_bkm.addWidget(canvas)

    log_zone = QTextEdit()
    log_zone.setReadOnly(True)
    log_zone.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px; ""background: #1e1e1e; color: #d4d4d4; border-radius: 6px; ""padding: 8px;")
    log_zone.setPlainText("\n".join(logs))
    # Scroll en bas pour voir la fin
    sb = log_zone.verticalScrollBar()
    sb.setValue(sb.maximum())
    layout_bkm.addWidget(log_zone)

    # bouton "Suite → Dendrogramme"
    bouton_dendro = QPushButton("▶  Next - Dendrogram")
    bouton_dendro.setFixedHeight(42)
    bouton_dendro.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def dendro_clicked():
        fenetre_bkm.close()
        lancer_dendrogramme()
    bouton_dendro.clicked.connect(dendro_clicked)
    layout_bkm.addWidget(bouton_dendro)

    builtins._fenetre_bkm  = fenetre_bkm
    builtins._log_zone_bkm = log_zone
    fenetre_bkm.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE DENDROGRAMME
# ══════════════════════════════════════════════════════════════════════════════

def lancer_dendrogramme():
    """Lance run_dendrogramme() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Dendrogramme")
    fenetre_load.resize(440, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 220, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Dendrogramme ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_dendro = fenetre_load

    etat_dendro = {"fig": None, "termine": False}

    def run_dendro():
        try:
            etat_dendro["fig"] = pipeline.run_dendrogramme()
        finally:
            etat_dendro["termine"] = True

    threading.Thread(target=run_dendro, daemon=True).start()

    timer_dendro = QTimer()
    timer_dendro.setInterval(200)
    builtins._timer_dendro = timer_dendro

    def verifier_dendro():
        if etat_dendro["termine"]:
            timer_dendro.stop()
            fenetre_load.close()
            ouvrir_fenetre_dendrogramme(etat_dendro["fig"])

    timer_dendro.timeout.connect(verifier_dendro)
    timer_dendro.start()


def ouvrir_fenetre_dendrogramme(fig):
    """Affiche le dendrogramme dans une nouvelle fenêtre avec la barre matplotlib."""
    fenetre_dendro = QMainWindow()
    fenetre_dendro.setWindowTitle("imsCORE - Dendrogram")
    fenetre_dendro.resize(1200, 700)

    geo = QDesktopWidget().availableGeometry()
    fenetre_dendro.move(geo.center().x() - 600, geo.center().y() - 350)

    w = QWidget()
    fenetre_dendro.setCentralWidget(w)
    layout_dendro = QVBoxLayout(w)
    layout_dendro.setContentsMargins(10, 10, 10, 10)
    layout_dendro.setSpacing(6)

    if fig is not None:
        canvas  = FigureCanvasQTAgg(fig)
        toolbar = NavigationToolbar2QT(canvas, fenetre_dendro)
        layout_dendro.addWidget(toolbar)
        layout_dendro.addWidget(canvas)
    else:
        lbl_err = QLabel("No dendrograms to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_dendro.addWidget(lbl_err)

    bouton_cartes = QPushButton("▶  Next - Spatial map")
    bouton_cartes.setFixedHeight(42)
    bouton_cartes.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def cartes_clicked():
        fenetre_dendro.close()
        lancer_cartes_spatiales()
    bouton_cartes.clicked.connect(cartes_clicked)
    layout_dendro.addWidget(bouton_cartes)

    builtins._fenetre_dendro = fenetre_dendro
    fenetre_dendro.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE CARTES SPATIALES
# ══════════════════════════════════════════════════════════════════════════════

def lancer_cartes_spatiales():
    """Lance run_cartes_spatiales() et run_all_cartes_spatiales() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Spatial map Loading")
    fenetre_load.resize(480, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 240, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳ Loading spatial map , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_cartes = fenetre_load

    etat_cartes = {"fig_cartes": None, "fig_all": None, "termine": False}

    def run_cartes():
        try:
            etat_cartes["fig_cartes"] = pipeline.run_cartes_spatiales()
            etat_cartes["fig_all"]    = pipeline.run_all_cartes_spatiales()
        finally:
            etat_cartes["termine"] = True

    threading.Thread(target=run_cartes, daemon=True).start()

    timer_cartes = QTimer()
    timer_cartes.setInterval(200)
    builtins._timer_cartes = timer_cartes

    def verifier_cartes():
        if etat_cartes["termine"]:
            timer_cartes.stop()
            fenetre_load.close()
            ouvrir_fenetre_cartes_spatiales(etat_cartes["fig_cartes"], etat_cartes["fig_all"])

    timer_cartes.timeout.connect(verifier_cartes)
    timer_cartes.start()


def ouvrir_fenetre_cartes_spatiales(fig_cartes, fig_all):
    """Affiche les deux figures de cartes spatiales dans une fenêtre scrollable."""
    fenetre_cartes = QMainWindow()
    fenetre_cartes.setWindowTitle("imsCORE - Spatial map")

    widget_central = QWidget()
    fenetre_cartes.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setStyleSheet("border: none;")

    contenu_scroll = QWidget()
    layout_scroll = QVBoxLayout(contenu_scroll)
    layout_scroll.setContentsMargins(10, 10, 10, 10)
    layout_scroll.setSpacing(20)

    if fig_cartes is not None:
        w_cartes = int(fig_cartes.get_figwidth()  * fig_cartes.dpi)
        h_cartes = int(fig_cartes.get_figheight() * fig_cartes.dpi)
        toolbar_cartes = NavigationToolbar2QT(FigureCanvasQTAgg(fig_cartes), fenetre_cartes)
        canvas_cartes  = FigureCanvasQTAgg(fig_cartes)
        canvas_cartes.setMinimumSize(w_cartes, h_cartes)
        layout_scroll.addWidget(toolbar_cartes)
        layout_scroll.addWidget(canvas_cartes)

    separateur = QFrame()
    separateur.setFrameShape(QFrame.HLine)
    separateur.setStyleSheet("color: #ddd; margin: 6px 0px;")
    layout_scroll.addWidget(separateur)

    if fig_all is not None:
        w_all = int(fig_all.get_figwidth()  * fig_all.dpi)
        h_all = int(fig_all.get_figheight() * fig_all.dpi)
        toolbar_all = NavigationToolbar2QT(FigureCanvasQTAgg(fig_all), fenetre_cartes)
        canvas_all  = FigureCanvasQTAgg(fig_all)
        canvas_all.setMinimumSize(w_all, h_all)
        layout_scroll.addWidget(toolbar_all)
        layout_scroll.addWidget(canvas_all)

    bouton_umap = QPushButton("▶  Next - UMAP")
    bouton_umap.setFixedHeight(42)
    bouton_umap.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def umap_clicked():
        fenetre_cartes.close()
        lancer_umap()
    bouton_umap.clicked.connect(umap_clicked)
    layout_scroll.addWidget(bouton_umap)

    zone_defilement.setWidget(contenu_scroll)
    layout_principal.addWidget(zone_defilement)

    builtins._fenetre_cartes = fenetre_cartes
    fenetre_cartes.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE UMAP
# ══════════════════════════════════════════════════════════════════════════════

def lancer_umap():
    """Lance run_UMAP() et run_all_UMAP() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading UMAP")
    fenetre_load.resize(480, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 240, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading UMAP , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_umap = fenetre_load

    etat_umap = {"fig_umap": None, "fig_all": None, "termine": False}

    def run_umap():
        try:
            etat_umap["fig_umap"] = pipeline.run_UMAP()
            etat_umap["fig_all"]  = pipeline.run_all_UMAP()
        finally:
            etat_umap["termine"] = True

    threading.Thread(target=run_umap, daemon=True).start()

    timer_umap = QTimer()
    timer_umap.setInterval(200)
    builtins._timer_umap = timer_umap

    def verifier_umap():
        if etat_umap["termine"]:
            timer_umap.stop()
            fenetre_load.close()
            ouvrir_fenetre_umap(etat_umap["fig_umap"], etat_umap["fig_all"])

    timer_umap.timeout.connect(verifier_umap)
    timer_umap.start()


def ouvrir_fenetre_umap(fig_umap, fig_all):
    """Affiche les deux figures UMAP dans une fenêtre scrollable."""
    fenetre_umap = QMainWindow()
    fenetre_umap.setWindowTitle("imsCORE - UMAP")

    widget_central = QWidget()
    fenetre_umap.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setStyleSheet("border: none;")

    contenu_scroll = QWidget()
    layout_scroll = QVBoxLayout(contenu_scroll)
    layout_scroll.setContentsMargins(10, 10, 10, 10)
    layout_scroll.setSpacing(20)

    if fig_umap is not None:
        w_umap = int(fig_umap.get_figwidth()  * fig_umap.dpi)
        h_umap = int(fig_umap.get_figheight() * fig_umap.dpi)
        toolbar_umap = NavigationToolbar2QT(FigureCanvasQTAgg(fig_umap), fenetre_umap)
        canvas_umap  = FigureCanvasQTAgg(fig_umap)
        canvas_umap.setMinimumSize(w_umap, h_umap)
        layout_scroll.addWidget(toolbar_umap)
        layout_scroll.addWidget(canvas_umap)

    separateur = QFrame()
    separateur.setFrameShape(QFrame.HLine)
    separateur.setStyleSheet("color: #ddd; margin: 6px 0px;")
    layout_scroll.addWidget(separateur)

    if fig_all is not None:
        w_all = int(fig_all.get_figwidth()  * fig_all.dpi)
        h_all = int(fig_all.get_figheight() * fig_all.dpi)
        toolbar_all = NavigationToolbar2QT(FigureCanvasQTAgg(fig_all), fenetre_umap)
        canvas_all  = FigureCanvasQTAgg(fig_all)
        canvas_all.setMinimumSize(w_all, h_all)
        layout_scroll.addWidget(toolbar_all)
        layout_scroll.addWidget(canvas_all)

    bouton_distrib = QPushButton("▶  Next - spatial distribution per sample / silhouette bar chart / violin per cluster")
    bouton_distrib.setFixedHeight(42)
    bouton_distrib.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def distrib_clicked():
        fenetre_umap.close()
        lancer_distrib_violin()
    bouton_distrib.clicked.connect(distrib_clicked)
    layout_scroll.addWidget(bouton_distrib)

    zone_defilement.setWidget(contenu_scroll)
    layout_principal.addWidget(zone_defilement)

    builtins._fenetre_umap = fenetre_umap
    fenetre_umap.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE DISTRIBUTION PAR ÉCHANTILLON / SILHOUETTE / VIOLIN
# ══════════════════════════════════════════════════════════════════════════════

def lancer_distrib_violin():
    """Lance run_multi_echantillons_bar_chart_violin() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading spatial distribution per sample / silhouette bar chart / violin per cluster")
    fenetre_load.resize(480, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 240, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading spatial distribution per sample / silhouette bar chart / violin per cluster , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_distrib = fenetre_load

    etat_distrib = {"fig1": None, "fig2": None, "fig3": None, "termine": False}

    def run_distrib():
        try:
            etat_distrib["fig1"], etat_distrib["fig2"], etat_distrib["fig3"] = pipeline.run_multi_echantillons_bar_chart_violin()
        finally:
            etat_distrib["termine"] = True

    threading.Thread(target=run_distrib, daemon=True).start()

    timer_distrib = QTimer()
    timer_distrib.setInterval(200)
    builtins._timer_distrib = timer_distrib

    def verifier_distrib():
        if etat_distrib["termine"]:
            timer_distrib.stop()
            fenetre_load.close()
            ouvrir_fenetre_distrib_violin(etat_distrib["fig1"], etat_distrib["fig2"], etat_distrib["fig3"])

    timer_distrib.timeout.connect(verifier_distrib)
    timer_distrib.start()


def ouvrir_fenetre_distrib_violin(fig1, fig2, fig3):
    """Affiche les figures de distribution par échantillon, silhouette et violin dans une fenêtre scrollable."""
    fenetre_distrib = QMainWindow()
    fenetre_distrib.setWindowTitle("imsCORE - spatial distribution per sample / silhouette bar chart / violin per cluster")

    widget_central = QWidget()
    fenetre_distrib.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setStyleSheet("border: none;")

    contenu_scroll = QWidget()
    layout_scroll = QVBoxLayout(contenu_scroll)
    layout_scroll.setContentsMargins(10, 10, 10, 10)
    layout_scroll.setSpacing(20)

    for fig in (fig1, fig2, fig3):
        if fig is not None:
            w_fig = int(fig.get_figwidth()  * fig.dpi)
            h_fig = int(fig.get_figheight() * fig.dpi)
            toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_distrib)
            canvas  = FigureCanvasQTAgg(fig)
            canvas.setMinimumSize(w_fig, h_fig)
            layout_scroll.addWidget(toolbar)
            layout_scroll.addWidget(canvas)

            separateur = QFrame()
            separateur.setFrameShape(QFrame.HLine)
            separateur.setStyleSheet("color: #ddd; margin: 6px 0px;")
            layout_scroll.addWidget(separateur)

    bouton_spectres = QPushButton("▶  Next - Average spectra per cluster")
    bouton_spectres.setFixedHeight(42)
    bouton_spectres.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def spectres_clicked():
        fenetre_distrib.close()
        lancer_spectres_moyens()
    bouton_spectres.clicked.connect(spectres_clicked)
    layout_scroll.addWidget(bouton_spectres)

    zone_defilement.setWidget(contenu_scroll)
    layout_principal.addWidget(zone_defilement)

    builtins._fenetre_distrib = fenetre_distrib
    fenetre_distrib.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# SPECTRES MOYENS PAR CLUSTER
# ══════════════════════════════════════════════════════════════════════════════

def lancer_spectres_moyens():
    """Lance run_spectre_moyen_cluster() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Average spectra per cluster")
    fenetre_load.resize(440, 120)
    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 220, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Average spectra , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_spectres = fenetre_load

    etat = {"fig": None, "termine": False}

    def run():
        try:
            etat["fig"] = pipeline.run_spectre_moyen_cluster()
        finally:
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_spectres = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_spectres_moyens(etat["fig"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_spectres_moyens(fig):
    """Affiche les spectres moyens par cluster dans une fenêtre scrollable."""
    fenetre_spectres = QMainWindow()
    fenetre_spectres.setWindowTitle("imsCORE - Average spectra per cluster")

    widget_central = QWidget()
    fenetre_spectres.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setStyleSheet("border: none;")

    contenu_scroll = QWidget()
    layout_scroll = QVBoxLayout(contenu_scroll)
    layout_scroll.setContentsMargins(10, 10, 10, 10)
    layout_scroll.setSpacing(10)

    if fig is not None:
        w_fig = int(fig.get_figwidth()  * fig.dpi)
        h_fig = int(fig.get_figheight() * fig.dpi)
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_spectres)
        canvas  = FigureCanvasQTAgg(fig)
        canvas.setMinimumSize(w_fig, h_fig)
        layout_scroll.addWidget(toolbar)
        layout_scroll.addWidget(canvas)
    else:
        lbl_err = QLabel("No spectra to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_scroll.addWidget(lbl_err)

    bouton_fenetre_spectres = QPushButton("▶  Next - discriminant m/z  / Kruskal-Wallis test")
    bouton_fenetre_spectres.setFixedHeight(42)
    bouton_fenetre_spectres.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")

    def bouton_spectres_clicked():
        fenetre_spectres.close()
        lancer_kruskal()

    bouton_fenetre_spectres.clicked.connect(bouton_spectres_clicked)
    layout_scroll.addWidget(bouton_fenetre_spectres)

    zone_defilement.setWidget(contenu_scroll)
    layout_principal.addWidget(zone_defilement)

    builtins._fenetre_spectres = fenetre_spectres
    fenetre_spectres.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# KRUSKAL-WALLIS
# ══════════════════════════════════════════════════════════════════════════════

def lancer_kruskal():
    """Lance run_to_pic_mz_test_kruskal_wallis() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Kruskal-Wallis")
    fenetre_load.resize(440, 120)
    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 220, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Kruskal-Wallis test , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_kruskal = fenetre_load

    etat = {"fig": None, "termine": False, "logs": []}

    def run():
        sys.stdout = types.SimpleNamespace(write=lambda txt: etat["logs"].append(txt.rstrip()) if txt.strip() else None, flush=lambda: None)
        try:
            etat["fig"] = pipeline.run_to_pic_mz_test_kruskal_wallis()
        finally:
            sys.stdout = sys.__stdout__
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_kruskal = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_kruskal(etat["fig"], etat["logs"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_kruskal(fig, logs=None):
    """Affiche les résultats Kruskal-Wallis dans une fenêtre scrollable."""
    fenetre_kruskal = QMainWindow()
    fenetre_kruskal.setWindowTitle("imsCORE - discriminant m/z / Kruskal-Wallis")

    widget_central = QWidget()
    fenetre_kruskal.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    zone_defilement = QScrollArea()
    zone_defilement.setWidgetResizable(True)
    zone_defilement.setStyleSheet("border: none;")

    contenu_scroll = QWidget()
    layout_scroll = QVBoxLayout(contenu_scroll)
    layout_scroll.setContentsMargins(10, 10, 10, 10)
    layout_scroll.setSpacing(10)

    if fig is not None:
        w_fig = int(fig.get_figwidth()  * fig.dpi)
        h_fig = int(fig.get_figheight() * fig.dpi)
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_kruskal)
        canvas  = FigureCanvasQTAgg(fig)
        canvas.setMinimumSize(w_fig, h_fig)
        layout_scroll.addWidget(toolbar)
        layout_scroll.addWidget(canvas)
    else:
        lbl_err = QLabel("No results to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_scroll.addWidget(lbl_err)

    zone_defilement.setWidget(contenu_scroll)
    zone_defilement.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    layout_principal.addWidget(zone_defilement, stretch=1)

    if logs:
        log_zone = QTextEdit()
        log_zone.setReadOnly(True)
        log_zone.setFixedHeight(120)
        log_zone.setStyleSheet("font-family: monospace; font-size: 11px; background-color: #1e1e2e; color: #cdd6f4; border: none; padding: 6px;")
        log_zone.setPlainText('\n'.join(logs))
        layout_principal.addWidget(log_zone)

    bouton_heatmap = QPushButton("▶  Next - Lipid heatmap")
    bouton_heatmap.setFixedHeight(42)
    bouton_heatmap.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def heatmap_clicked():
        fenetre_kruskal.close()
        lancer_heatmap()
    bouton_heatmap.clicked.connect(heatmap_clicked)
    layout_principal.addWidget(bouton_heatmap)

    builtins._fenetre_kruskal = fenetre_kruskal
    fenetre_kruskal.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# HEATMAP
# ══════════════════════════════════════════════════════════════════════════════

def lancer_heatmap():
    """Lance run_heatmap() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Heatmap")
    fenetre_load.resize(440, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 220, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading heatmap, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_heatmap = fenetre_load

    etat = {"fig": None, "termine": False}

    def run():
        try:
            etat["fig"] = pipeline.run_heatmap()
        finally:
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_heatmap = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_heatmap(etat["fig"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_heatmap(fig):
    """Affiche la heatmap lipidique dans une nouvelle fenêtre."""
    fenetre_heatmap = QMainWindow()
    fenetre_heatmap.setWindowTitle("imsCORE - Lipid heatmap")

    widget_central = QWidget()
    fenetre_heatmap.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(10, 10, 10, 10)
    layout_principal.setSpacing(6)

    if fig is not None:
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_heatmap)
        canvas  = FigureCanvasQTAgg(fig)
        layout_principal.addWidget(toolbar)
        layout_principal.addWidget(canvas)
    else:
        lbl_err = QLabel("No heatmaps to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_principal.addWidget(lbl_err)

    bouton_ions = QPushButton("▶  Next - Discriminant Ion Spatial Maps")
    bouton_ions.setFixedHeight(42)
    bouton_ions.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def ions_clicked():
        fenetre_heatmap.close()
        lancer_cartes_ions()
    bouton_ions.clicked.connect(ions_clicked)
    layout_principal.addWidget(bouton_ions)

    builtins._fenetre_heatmap = fenetre_heatmap
    fenetre_heatmap.showMaximized()

# ══════════════════════════════════════════════════════════════════════════════
# Cartes spatiales des ions les plus discriminants
# ══════════════════════════════════════════════════════════════════════════════

def lancer_cartes_ions():
    """Lance run_cartes_ions_discriminants() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Discriminant Ion Spatial Maps")
    fenetre_load.resize(500, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 250, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Discriminant Ion Spatial Maps, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_cartes_ions = fenetre_load

    etat = {"fig": None, "termine": False}

    def run():
        try:
            etat["fig"] = pipeline.run_cartes_ions_discriminants()
        finally:
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_cartes_ions = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_cartes_ions(etat["fig"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_cartes_ions(fig):
    """Affiche les cartes spatiales des ions discriminants dans une nouvelle fenêtre."""
    fenetre_cartes_ions = QMainWindow()
    fenetre_cartes_ions.setWindowTitle("imsCORE - Discriminant Ion Spatial Maps")

    widget_central = QWidget()
    fenetre_cartes_ions.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(10, 10, 10, 10)
    layout_principal.setSpacing(6)

    if fig is not None:
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_cartes_ions)
        canvas  = FigureCanvasQTAgg(fig)
        layout_principal.addWidget(toolbar)
        layout_principal.addWidget(canvas)
    else:
        lbl_err = QLabel("Can't load spatial map.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_principal.addWidget(lbl_err)

    bouton_export = QPushButton("▶  Next - CSV exports ")
    bouton_export.setFixedHeight(42)
    bouton_export.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def export_clicked():
        fenetre_cartes_ions.close()
        ouvrir_fenetre_export_csv()
    bouton_export.clicked.connect(export_clicked)
    layout_principal.addWidget(bouton_export)

    builtins._fenetre_cartes_ions = fenetre_cartes_ions
    fenetre_cartes_ions.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE EXPORT CSV
# ══════════════════════════════════════════════════════════════════════════════

def ouvrir_fenetre_export_csv():
    """Fenêtre permettant à l'utilisateur de choisir un dossier de destination pour l'export CSV."""
    fenetre_export = QMainWindow()
    fenetre_export.setWindowTitle("imsCORE - CSV export")
    fenetre_export.resize(600, 340)

    geo = QDesktopWidget().availableGeometry()
    fenetre_export.move(geo.center().x() - 300, geo.center().y() - 170)

    widget_central = QWidget()
    fenetre_export.setCentralWidget(widget_central)
    disposition = QVBoxLayout(widget_central)
    disposition.setSpacing(20)
    disposition.setContentsMargins(40, 40, 40, 40)

    titre = QLabel("CSV Exports")
    titre.setAlignment(Qt.AlignCenter)
    titre.setStyleSheet("font-size: 23px; font-weight: bold;")
    disposition.addWidget(titre)

    explication = QLabel(
        "The analysis is done. You can now export results.\n\n"
        "Three CSV files will be created in the selected folder :\n"
        "  • Pixels - coordinates, cluster, TIC, UMAP, PCA, and spectra\n"
        "  • Average spectra - mean and standard deviation by cluster\n"
        "  • Discriminant Pics - Significant Ions by Cluster (Kruskal-Wallis)\n"
        "Once the exports are done , a full recap will be shown on screen"
    )
    explication.setAlignment(Qt.AlignCenter)
    explication.setStyleSheet("font-size: 13px; color: #555;")
    explication.setWordWrap(True)
    disposition.addWidget(explication)

    disposition.addStretch()

    bouton_dossier = QPushButton("📂  Choose a folder for the exports")
    bouton_dossier.setFixedHeight(45)
    bouton_dossier.setStyleSheet("""QPushButton { font-size: 14px; background-color: #27AE60; color: white; border-radius: 8px; } QPushButton:hover { background-color: #1E8449; }""")

    def choisir_dossier_et_exporter():
        dossier = QFileDialog.getExistingDirectory(fenetre_export, "Choose a folder", "")
        if dossier:
            pipeline.chemin_export_csv = dossier
            fenetre_export.close()
            lancer_export_csv()

    bouton_dossier.clicked.connect(choisir_dossier_et_exporter)
    disposition.addWidget(bouton_dossier)

    disposition.addStretch()

    builtins._fenetre_export = fenetre_export
    fenetre_export.show()


def lancer_export_csv():
    """Lance run_csv_export() en arrière-plan avec une fenêtre de chargement."""
    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Running Exports")
    fenetre_load.resize(420, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 210, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Running CSV exports , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_export = fenetre_load

    etat = {"logs": [], "termine": False}

    sys.stdout = types.SimpleNamespace(write=lambda txt: etat["logs"].append(txt.rstrip()) if txt.strip() else None, flush=lambda: None)

    def run():
        pipeline.run_csv_export()
        etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_export = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            sys.stdout = sys.__stdout__
            fenetre_load.close()
            ouvrir_fenetre_recap()

    timer.timeout.connect(verifier)
    timer.start()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE RÉCAPITULATIF FINAL
# ══════════════════════════════════════════════════════════════════════════════

def ouvrir_fenetre_recap():
    """Affiche un récapitulatif graphique de l'analyse complète ."""
    fenetre_recap = QMainWindow()
    fenetre_recap.setWindowTitle("imsCORE - Final Recap")
    fenetre_recap.resize(780, 780)

    geo = QDesktopWidget().availableGeometry()
    fenetre_recap.move(geo.center().x() - 390, geo.center().y() - 390)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    fenetre_recap.setCentralWidget(scroll_area)

    widget_contenu = QWidget()
    scroll_area.setWidget(widget_contenu)
    disposition = QVBoxLayout(widget_contenu)
    disposition.setContentsMargins(40, 30, 40, 30)
    disposition.setSpacing(6)

    titre = QLabel("Recap - Bisecting K-Means MALDI-MSI")
    titre.setAlignment(Qt.AlignCenter)
    titre.setStyleSheet("font-size: 22px; font-weight: bold; color: #2C3E50; padding: 10px 0 4px 0;")
    disposition.addWidget(titre)

    separateur_haut = QFrame()
    separateur_haut.setFrameShape(QFrame.HLine)
    separateur_haut.setStyleSheet("color: #BDC3C7; margin-bottom: 8px;")
    disposition.addWidget(separateur_haut)

    def ajouter_ligne(texte_gauche, texte_droite, gras=False, fond="#FAFAFA"):
        """Fonction utilitaire pour créer une ligne label/valeur"""
        ligne = QWidget()
        ligne.setStyleSheet(f"background-color: {fond}; border-radius: 4px;")
        lay = QHBoxLayout(ligne)
        lay.setContentsMargins(14, 6, 14, 6)
        lbl_g = QLabel(texte_gauche)
        lbl_d = QLabel(texte_droite)
        poids = "600" if gras else "400"
        lbl_g.setStyleSheet(f"font-size: 13px; font-weight: {poids}; color: #2C3E50; background: transparent;")
        lbl_d.setStyleSheet(f"font-size: 13px; color: #555; background: transparent;")
        lbl_d.setAlignment(Qt.AlignRight)
        lay.addWidget(lbl_g)
        lay.addStretch()
        lay.addWidget(lbl_d)
        disposition.addWidget(ligne)

    def ajouter_section(texte):
        lbl = QLabel(texte)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #4A90D9; padding: 10px 0 2px 0; background: transparent;")
        disposition.addWidget(lbl)

    ajouter_section("📁  File(s)")
    ajouter_ligne("Number of file(s)", str(len(pipeline.IMZML_FILES)), gras=True)
    for f in pipeline.IMZML_FILES:
        ajouter_ligne("  •  " + os.path.basename(f), "", fond="#F4F6F8")

    # Paramètres m/z
    ajouter_section("📊 m/z settings")
    ajouter_ligne("m/z Range", f"[{pipeline.MZ_MIN}, {pipeline.MZ_MAX}] Da", gras=True)
    ajouter_ligne("Bin size", f"{pipeline.MZ_BIN_SIZE} Da", fond="#F4F6F8")
    ajouter_ligne("Number of bins", str(pipeline.N_BINS))
    ajouter_ligne("Preserved ions", f"{int(pipeline.ion_keep.sum())} / {pipeline.N_BINS}  (prevalence ≥ {pipeline.ION_MIN_PREVALENCE*100:.0f}%)", fond="#F4F6F8")
    ajouter_ligne("Significant ions (KW)", f"{int(pipeline.sig_mask.sum())}  (p < 0.01)")

    # Pixels
    ajouter_section("🧩  Pixels")
    ajouter_ligne("Total pixels", str(pipeline.n_pixels), gras=True, fond="#F4F6F8")
    ajouter_ligne("mask pixels", f"{pipeline.n_tissue}  ({pipeline.n_tissue / pipeline.n_pixels * 100:.1f}%)")


    # PCA & Clustering
    ajouter_section("🔬  PCA & Clustering")
    ajouter_ligne("PCA Components", str(pipeline.N_PCA_COMPONENTS), fond="#F4F6F8")
    ajouter_ligne("Final clusters", str(pipeline.n_clusters), gras=True)

    ajouter_ligne("Local Silhouette Threshold", str(pipeline.SILHOUETTE_THRESHOLD), fond="#F4F6F8")
    if pipeline.tree_log:
        ajouter_ligne("Accepted bisections", str(len(pipeline.tree_log)))
        best = max(pipeline.tree_log, key=lambda h: h["sil_local"])
        ajouter_ligne("Best Local silhouette score", f"{best['sil_local']:.4f}  (step {best['step']})", fond="#F4F6F8")
    sil_moy = float(np.mean(pipeline.silhouette_samples(pipeline.spec_pca, pipeline.labels_tissue)))
    ajouter_ligne("Overall Average Silhouette score", f"{sil_moy:.4f}", gras=True)


    # Exports 
    ajouter_section("💾  CSV Exports")
    ajouter_ligne("Pixels file",   pipeline.CSV_PIXELS,  fond="#F4F6F8")
    ajouter_ligne("Spectras file", pipeline.CSV_SPECTRA)
    ajouter_ligne("Peaks file",     pipeline.CSV_PEAKS,   fond="#F4F6F8")

    # Distribution des clusters
    ajouter_section("📈  Cluster Distribution")
    for cid in pipeline.unique_clusters:
        n   = int((pipeline.labels_tissue == cid).sum())
        pct = n / pipeline.n_tissue * 100
        nb_blocs = int(pct / 2)
        barre_txt = "█" * nb_blocs + "░" * (25 - nb_blocs)
        ajouter_ligne(f"  Cluster {cid}", f"{n} px  ({pct:.1f}%)  {barre_txt}", fond="#F4F6F8" if cid % 2 == 0 else "#FAFAFA")

    separateur_bas = QFrame()
    separateur_bas.setFrameShape(QFrame.HLine)
    separateur_bas.setStyleSheet("color: #BDC3C7; margin-top: 12px;")
    disposition.addWidget(separateur_bas)

    bouton_quitter = QPushButton("Close app")
    bouton_quitter.setFixedHeight(46)
    bouton_quitter.setStyleSheet("""QPushButton {font-size: 14px;font-weight: bold;background-color: #E8E8E8;color: #2C3E50;border-radius: 8px;margin-top: 10px;}QPushButton:hover {background-color: #E74C3C;color: white;}""")
    bouton_quitter.clicked.connect(QApplication.instance().quit)
    disposition.addWidget(bouton_quitter)

    builtins._fenetre_recap = fenetre_recap
    fenetre_recap.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE LABEL MAPS (PKL)
# ══════════════════════════════════════════════════════════════════════════════

def lancer_label_maps():
    """Lance run_label_maps() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Label Maps")
    fenetre_load.resize(460, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 230, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Label Maps, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_label_maps = fenetre_load

    etat = {"fig": None, "termine": False}

    def run():
        try:
            etat["fig"] = pipeline.run_label_maps()
        finally:
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_label_maps = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_label_maps(etat["fig"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_label_maps(fig):
    """Affiche les label maps PKL dans une nouvelle fenêtre."""
    fenetre_lm = QMainWindow()
    fenetre_lm.setWindowTitle("imsCORE - Label Maps")

    widget_central = QWidget()
    fenetre_lm.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(10, 10, 10, 10)
    layout_principal.setSpacing(6)

    if fig is not None:
        w_fig = int(fig.get_figwidth() * fig.dpi)
        h_fig = int(fig.get_figheight() * fig.dpi)
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_lm)
        canvas  = FigureCanvasQTAgg(fig)
        canvas.setMinimumSize(w_fig, h_fig)
        layout_principal.addWidget(toolbar)
        layout_principal.addWidget(canvas)
    else:
        lbl_err = QLabel("No label maps to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_principal.addWidget(lbl_err)

    bouton_ratios = QPushButton("▶  Next - Label Ratios")
    bouton_ratios.setFixedHeight(42)
    bouton_ratios.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def ratios_clicked():
        fenetre_lm.close()
        lancer_label_ratios()
    bouton_ratios.clicked.connect(ratios_clicked)
    layout_principal.addWidget(bouton_ratios)

    builtins._fenetre_label_maps = fenetre_lm
    fenetre_lm.showMaximized()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE LABEL RATIOS (PKL)
# ══════════════════════════════════════════════════════════════════════════════

def lancer_label_ratios():
    """Lance run_label_ratios() en arrière-plan avec une fenêtre de chargement."""

    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Loading Label Ratios")
    fenetre_load.resize(460, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 230, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Loading Label Ratios, please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_label_ratios = fenetre_load

    etat = {"fig": None, "df": None, "termine": False, "logs": []}

    sys.stdout = types.SimpleNamespace(
        write=lambda txt: etat["logs"].append(txt.rstrip()) if txt.strip() else None,
        flush=lambda: None
    )

    def run():
        try:
            etat["fig"], etat["df"] = pipeline.run_label_ratios()
        finally:
            sys.stdout = sys.__stdout__
            etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_label_ratios = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            fenetre_load.close()
            ouvrir_fenetre_label_ratios(etat["fig"], etat["df"], etat["logs"])

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_label_ratios(fig, df_ratios, logs):
    """Affiche le bar chart des ratios PKL et un tableau récapitulatif."""
    fenetre_lr = QMainWindow()
    fenetre_lr.setWindowTitle("imsCORE - Label Ratios")
    fenetre_lr.resize(800, 700)

    geo = QDesktopWidget().availableGeometry()
    fenetre_lr.move(geo.center().x() - 400, geo.center().y() - 350)

    widget_central = QWidget()
    fenetre_lr.setCentralWidget(widget_central)
    layout_principal = QVBoxLayout(widget_central)
    layout_principal.setContentsMargins(10, 10, 10, 10)
    layout_principal.setSpacing(6)

    if fig is not None:
        toolbar = NavigationToolbar2QT(FigureCanvasQTAgg(fig), fenetre_lr)
        canvas  = FigureCanvasQTAgg(fig)
        layout_principal.addWidget(toolbar)
        layout_principal.addWidget(canvas)
    else:
        lbl_err = QLabel("No ratio chart to display.")
        lbl_err.setAlignment(Qt.AlignCenter)
        lbl_err.setStyleSheet("font-size: 13px; color: #999;")
        layout_principal.addWidget(lbl_err)

    if logs:
        log_zone = QTextEdit()
        log_zone.setReadOnly(True)
        log_zone.setFixedHeight(120)
        log_zone.setStyleSheet("font-family: monospace; font-size: 11px; background: #1e1e1e; color: #ccc; border-radius: 4px;")
        log_zone.setPlainText("\n".join(logs))
        layout_principal.addWidget(log_zone)

    bouton_recap = QPushButton("▶  Next - CSV export")
    bouton_recap.setFixedHeight(42)
    bouton_recap.setStyleSheet("""QPushButton { font-size: 13px; background-color: #4A90D9; color: white; border-radius: 8px; margin: 6px 10px; } QPushButton:hover { background-color: #357ABD; }""")
    def suite_recap_clicked():
        fenetre_lr.close()
        ouvrir_fenetre_export_csv_pkl(df_ratios)
    bouton_recap.clicked.connect(suite_recap_clicked)
    layout_principal.addWidget(bouton_recap)

    builtins._fenetre_label_ratios = fenetre_lr
    fenetre_lr.show()


# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE EXPORT CSV (LABEL RATIOS)
# ══════════════════════════════════════════════════════════════════════════════

def ouvrir_fenetre_export_csv_pkl(df_ratios):
    """Fenêtre permettant à l'utilisateur de choisir un dossier de destination pour l'export CSV des label ratios."""
    fenetre_export = QMainWindow()
    fenetre_export.setWindowTitle("imsCORE - CSV export")
    fenetre_export.resize(600, 340)

    geo = QDesktopWidget().availableGeometry()
    fenetre_export.move(geo.center().x() - 300, geo.center().y() - 170)

    widget_central = QWidget()
    fenetre_export.setCentralWidget(widget_central)
    disposition = QVBoxLayout(widget_central)
    disposition.setSpacing(20)
    disposition.setContentsMargins(40, 40, 40, 40)

    titre = QLabel("CSV Export")
    titre.setAlignment(Qt.AlignCenter)
    titre.setStyleSheet("font-size: 23px; font-weight: bold;")
    disposition.addWidget(titre)

    explication = QLabel(
        "The analysis is done. You can now export the results.\n\n"
        "A CSV file containing the label ratios will be created in the selected folder.\n"
        "Once the export is done , a full recap will be shown on screen"
    )
    explication.setAlignment(Qt.AlignCenter)
    explication.setStyleSheet("font-size: 13px; color: #555;")
    explication.setWordWrap(True)
    disposition.addWidget(explication)

    disposition.addStretch()

    bouton_dossier = QPushButton("📂  Choose a folder for the export")
    bouton_dossier.setFixedHeight(45)
    bouton_dossier.setStyleSheet("""QPushButton { font-size: 14px; background-color: #27AE60; color: white; border-radius: 8px; } QPushButton:hover { background-color: #1E8449; }""")

    def choisir_dossier_et_exporter():
        dossier = QFileDialog.getExistingDirectory(fenetre_export, "Choose a folder", "")
        if dossier:
            pipeline.chemin_export_csv = dossier
            fenetre_export.close()
            lancer_export_csv_pkl(df_ratios)

    bouton_dossier.clicked.connect(choisir_dossier_et_exporter)
    disposition.addWidget(bouton_dossier)

    disposition.addStretch()

    builtins._fenetre_export_pkl = fenetre_export
    fenetre_export.show()


def lancer_export_csv_pkl(df_ratios):
    """Lance run_csv_export_label_ratios() en arrière-plan avec une fenêtre de chargement."""
    fenetre_load = QMainWindow()
    fenetre_load.setWindowTitle("imsCORE - Running Export")
    fenetre_load.resize(420, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_load.move(geo.center().x() - 210, geo.center().y() - 60)

    w = QWidget()
    fenetre_load.setCentralWidget(w)
    layout_load = QVBoxLayout(w)
    layout_load.setContentsMargins(30, 24, 30, 20)
    layout_load.setSpacing(10)

    lbl_load = QLabel("⏳  Running CSV export , please wait ...")
    lbl_load.setAlignment(Qt.AlignCenter)
    lbl_load.setStyleSheet("font-size: 13px; color: #555;")

    barre_load = QProgressBar()
    barre_load.setObjectName("barre")
    barre_load.setRange(0, 0)
    barre_load.setTextVisible(False)
    barre_load.setFixedHeight(6)

    layout_load.addWidget(lbl_load)
    layout_load.addWidget(barre_load)
    fenetre_load.show()
    builtins._fenetre_load_export_pkl = fenetre_load

    etat = {"logs": [], "termine": False}

    sys.stdout = types.SimpleNamespace(write=lambda txt: etat["logs"].append(txt.rstrip()) if txt.strip() else None, flush=lambda: None)

    def run():
        pipeline.run_csv_export_label_ratios()
        etat["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer = QTimer()
    timer.setInterval(200)
    builtins._timer_export_pkl = timer

    def verifier():
        if etat["termine"]:
            timer.stop()
            sys.stdout = sys.__stdout__
            fenetre_load.close()
            ouvrir_fenetre_recap_pkl(df_ratios)

    timer.timeout.connect(verifier)
    timer.start()


def ouvrir_fenetre_recap_pkl(df_ratios):
    """Affiche un récapitulatif de l'analyse PKL."""
    fenetre_recap_pkl = QMainWindow()
    fenetre_recap_pkl.setWindowTitle("imsCORE - Final Recap")
    fenetre_recap_pkl.resize(780, 600)

    geo = QDesktopWidget().availableGeometry()
    fenetre_recap_pkl.move(geo.center().x() - 390, geo.center().y() - 300)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.NoFrame)
    fenetre_recap_pkl.setCentralWidget(scroll_area)

    widget_contenu = QWidget()
    scroll_area.setWidget(widget_contenu)
    disposition = QVBoxLayout(widget_contenu)
    disposition.setContentsMargins(40, 30, 40, 30)
    disposition.setSpacing(6)

    titre = QLabel("Recap - PKL Model Analysis")
    titre.setAlignment(Qt.AlignCenter)
    titre.setStyleSheet("font-size: 22px; font-weight: bold; color: #2C3E50; padding: 10px 0 4px 0;")
    disposition.addWidget(titre)

    sep_haut = QFrame()
    sep_haut.setFrameShape(QFrame.HLine)
    sep_haut.setStyleSheet("color: #BDC3C7; margin-bottom: 8px;")
    disposition.addWidget(sep_haut)

    def ajouter_ligne(texte_gauche, texte_droite, gras=False, fond="#FAFAFA"):
        ligne = QWidget()
        ligne.setStyleSheet(f"background-color: {fond}; border-radius: 4px;")
        lay = QHBoxLayout(ligne)
        lay.setContentsMargins(14, 6, 14, 6)
        lbl_g = QLabel(texte_gauche)
        lbl_d = QLabel(texte_droite)
        poids = "600" if gras else "400"
        lbl_g.setStyleSheet(f"font-size: 13px; font-weight: {poids}; color: #2C3E50; background: transparent;")
        lbl_d.setStyleSheet(f"font-size: 13px; color: #555; background: transparent;")
        lbl_d.setAlignment(Qt.AlignRight)
        lay.addWidget(lbl_g)
        lay.addStretch()
        lay.addWidget(lbl_d)
        disposition.addWidget(ligne)

    def ajouter_section(texte):
        lbl = QLabel(texte)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #4A90D9; padding: 10px 0 2px 0; background: transparent;")
        disposition.addWidget(lbl)

    ajouter_section("📁  Files")
    ajouter_ligne("imzML file", os.path.basename(pipeline.IMZML_FILES[0]), gras=True)
    ajouter_ligne("PKL model", os.path.basename(pipeline.chemin_pkl), fond="#F4F6F8")

    ajouter_section("📊  Analysis Parameters")
    ajouter_ligne("m/z Range", f"[{pipeline.MZ_MIN}, {pipeline.MZ_MAX}] Da", gras=True)
    ajouter_ligne("Max intensity size", str(pipeline.max_intensity_size), fond="#F4F6F8")

    ajouter_section("🏷️  Model Labels & Ratios")
    if df_ratios is not None:
        dominant = df_ratios["Ratio"].idxmax()
        ajouter_ligne("Number of labels", str(len(df_ratios)), gras=True)
        ajouter_ligne("Dominant label", f"{dominant}  ({df_ratios.loc[dominant, 'Ratio']:.3f})", fond="#F4F6F8")
        for i, label in enumerate(df_ratios.index):
            ratio_val = df_ratios.loc[label, "Ratio"]
            nb_blocs  = int(ratio_val * 25)
            barre_txt = "█" * nb_blocs + "░" * (25 - nb_blocs)
            fond_ligne = "#F4F6F8" if i % 2 == 0 else "#FAFAFA"
            ajouter_ligne(f"  •  {label}", f"{ratio_val:.4f}  ({ratio_val*100:.1f}%)  {barre_txt}", fond=fond_ligne)
    else:
        ajouter_ligne("Ratios", "Not available", fond="#F4F6F8")

    sep_bas = QFrame()
    sep_bas.setFrameShape(QFrame.HLine)
    sep_bas.setStyleSheet("color: #BDC3C7; margin-top: 12px;")
    disposition.addWidget(sep_bas)

    bouton_quitter = QPushButton("Close app")
    bouton_quitter.setFixedHeight(46)
    bouton_quitter.setStyleSheet("""QPushButton {font-size: 14px;font-weight: bold;background-color: #E8E8E8;color: #2C3E50;border-radius: 8px;margin-top: 10px;}QPushButton:hover {background-color: #E74C3C;color: white;}""")
    bouton_quitter.clicked.connect(QApplication.instance().quit)
    disposition.addWidget(bouton_quitter)

    builtins._fenetre_recap_pkl = fenetre_recap_pkl
    fenetre_recap_pkl.show()


# ══════════════════════════════════════════════════════════════════════════════
# LANCEMENT DU PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def lancer_pipeline():
    "fonction gerant le lancement du debut du programme (chargement de l'imZML + TIC MAP)"
    fenetre_run = QMainWindow()
    fenetre_run.setWindowTitle("imsCORE - Analysing data")
    fenetre_run.resize(420, 120)

    geo = QDesktopWidget().availableGeometry()
    fenetre_run.move(geo.center().x() - 210, geo.center().y() - 60)

    w = QWidget()
    fenetre_run.setCentralWidget(w)
    layout_run = QVBoxLayout(w)
    layout_run.setContentsMargins(30, 24, 30, 20)
    layout_run.setSpacing(10)

    lbl_run = QLabel("⏳  Analysing data , please wait ...")
    lbl_run.setAlignment(Qt.AlignCenter)
    lbl_run.setStyleSheet("font-size: 13px; color: #555;")

    barre_run = QProgressBar()
    barre_run.setObjectName("barre")
    barre_run.setRange(0, 0)
    barre_run.setTextVisible(False)
    barre_run.setFixedHeight(6)

    layout_run.addWidget(lbl_run)
    layout_run.addWidget(barre_run)
    fenetre_run.show()

    builtins._fenetre_run = fenetre_run

    # ont accumule les logs (dans notre cas les print) des taches en arriere plan dans une liste dans une liste pour pouvoir ensuite afficher les logs dans la fenetre
    etat_run = {"fig": None, "termine": False, "logs": []}

    
    sys.stdout = types.SimpleNamespace(write=lambda txt: etat_run["logs"].append(txt.rstrip()) if txt.strip() else None,flush=lambda: None)

    def run():
        pipeline.run_chargement_imzml()
        etat_run["fig"] = pipeline.run_tic_map()
        etat_run["termine"] = True

    threading.Thread(target=run, daemon=True).start()

    timer_run = QTimer()
    timer_run.setInterval(200)
    builtins._timer_run = timer_run

    def verifier_run():
        if etat_run["termine"]:
            timer_run.stop()
            sys.stdout = sys.__stdout__
            fenetre_run.close()
            ouvrir_fenetre_resultats(etat_run["fig"], etat_run["logs"])

    timer_run.timeout.connect(verifier_run)
    timer_run.start()

# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE CHOIX DES PARAMÈTRES
# ══════════════════════════════════════════════════════════════════════════════

def ouvrir_fenetre_parametres():
    """Gestion de l'ouverture de la fenetre paramètre"""
    fenetre_params = QMainWindow()
    fenetre_params.setWindowTitle("imsCORE")
    fenetre_params.resize(600, 420)

    widget_central = QWidget()
    fenetre_params.setCentralWidget(widget_central)
    disposition = QVBoxLayout(widget_central)
    disposition.setSpacing(20)
    disposition.setContentsMargins(40, 40, 40, 40)

    titre = QLabel("imsCORE")
    titre.setAlignment(Qt.AlignCenter)
    titre.setStyleSheet("font-size: 23px; font-weight: bold;")
    disposition.addWidget(titre)

    explication = QLabel(
        "Choose what setting to use for the analysis :\n\n"
        "• Default settings : start the analysis with chosen values\n"
        "• Custom settings : allow you to choose each setting before starting the analysis"
    )
    explication.setAlignment(Qt.AlignCenter)
    explication.setStyleSheet("font-size: 13px; color: #555;")
    explication.setWordWrap(True)
    disposition.addWidget(explication)

    disposition.addStretch()

    disposition_boutons = QHBoxLayout()
    disposition_boutons.setSpacing(20)

    bouton_defaut = QPushButton("✅  Default settings")
    bouton_perso  = QPushButton("⚙️  Custom settings")

    for bouton, couleur in [(bouton_defaut, "#27AE60"), (bouton_perso, "#E67E22")]:
        bouton.setFixedHeight(45)
        bouton.setStyleSheet(f"""QPushButton {{ font-size: 13px; background-color: {couleur}; color: white; border-radius: 8px; }} QPushButton:hover {{ background-color: {couleur}CC; }}""")

    def lancer_analyse():
        fenetre_params.close()
        lancer_pipeline()

    bouton_defaut.clicked.connect(lancer_analyse)
    bouton_perso.clicked.connect(lambda: fenetre_params_perso(fenetre_params))

    disposition_boutons.addWidget(bouton_defaut)
    disposition_boutons.addWidget(bouton_perso)
    disposition.addLayout(disposition_boutons)

    disposition.addStretch()

    fenetre_params.show()
    return fenetre_params

# ══════════════════════════════════════════════════════════════════════════════
# FENÊTRE DE CHOIX SEGMENTATION / CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

fenetre_choix = QMainWindow()
fenetre_choix.setWindowTitle("imsCORE")
fenetre_choix.resize(600, 300)

widget_central_choix = QWidget()
fenetre_choix.setCentralWidget(widget_central_choix)
disposition_choix = QVBoxLayout(widget_central_choix)
disposition_choix.setSpacing(20)
disposition_choix.setContentsMargins(40, 40, 40, 40)

titre_choix = QLabel("imsCORE")
titre_choix.setAlignment(Qt.AlignCenter)
titre_choix.setStyleSheet("font-size: 23px; font-weight: bold;")
disposition_choix.addWidget(titre_choix)

description_choix = QLabel(
    "Choose your analysis by clicking it's corresponding button"
)
description_choix.setAlignment(Qt.AlignCenter)
description_choix.setStyleSheet("font-size: 13px; color: #555;")
description_choix.setWordWrap(True)
disposition_choix.addWidget(description_choix)

disposition_choix.addStretch()

reference_fenetre2 = None
fichiers_selectionnes = []
chemin_pkl_selectionne = ""
mode_analyse = ""
fenetre_chargement = None
bouton_lancer = None
bouton_charger_pkl = None

def maj_bouton_lancer():
    if mode_analyse == "classification":
        bouton_lancer.setEnabled(len(fichiers_selectionnes) > 0 and chemin_pkl_selectionne != "")
    else:
        bouton_lancer.setEnabled(len(fichiers_selectionnes) > 0)

def ouvrir_fichiers():
    while True:
        chemin, _ = QFileDialog.getOpenFileName(fenetre_chargement, "Open imzML file", "", "imzML file (*.imzML)")
        if not chemin:
            break
        chemin = os.path.normpath(chemin)
        if chemin not in fichiers_selectionnes:
            fichiers_selectionnes.append(chemin)
        maj_bouton_lancer()
        reponse = QMessageBox.question(fenetre_chargement,"Add another file ?",f"{len(fichiers_selectionnes)} file(s) loaded.\nDo you want to add another file ?",QMessageBox.Yes | QMessageBox.No)
        if reponse == QMessageBox.No:
            break

def ouvrir_fichiers_pkl():
    global chemin_pkl_selectionne
    chemin_pkl, _ = QFileDialog.getOpenFileName(fenetre_chargement, "Open pkl file", "", "pkl file (*.pkl)")
    if chemin_pkl:
        chemin_pkl_selectionne = os.path.normpath(chemin_pkl)
        QMessageBox.information(fenetre_chargement, "PKL file loaded", f"Model loaded")
        maj_bouton_lancer()

def lancer_analyse_fichiers():
    global reference_fenetre2
    if len(fichiers_selectionnes) == 1:
        pipeline.IMZML_INPUT = str(fichiers_selectionnes[0])
    else:
        pipeline.IMZML_INPUT = [str(f) for f in fichiers_selectionnes]
    pipeline.chemin_pkl = chemin_pkl_selectionne
    fenetre_chargement.close()
    reference_fenetre2 = ouvrir_fenetre_parametres()

def ouvrir_fenetre_chargement(mode):
    global mode_analyse, fenetre_chargement, bouton_lancer, bouton_charger_pkl

    mode_analyse = mode
    fenetre_choix.close()

    fenetre_chargement = QMainWindow()
    fenetre_chargement.setWindowTitle("imsCORE")
    fenetre_chargement.resize(600, 400)

    widget_central = QWidget()
    fenetre_chargement.setCentralWidget(widget_central)
    disposition_principale = QVBoxLayout(widget_central)
    disposition_principale.setSpacing(20)
    disposition_principale.setContentsMargins(40, 40, 40, 40)

    titre_principal = QLabel("imsCORE")
    titre_principal.setAlignment(Qt.AlignCenter)
    titre_principal.setStyleSheet("font-size: 23px; font-weight: bold;")
    disposition_principale.addWidget(titre_principal)

    if mode == "classification":
        description = QLabel("Load an .imzml file and a .pkl file in order to start the analysis")
    else:
        description = QLabel("Load at least one .imzml file in order to start the analysis")
    
    description.setAlignment(Qt.AlignCenter)
    description.setStyleSheet("font-size: 13px; color: #555;")
    description.setWordWrap(True)
    disposition_principale.addWidget(description)

    disposition_principale.addStretch()

    bouton_lancer = QPushButton("▶  Start analysis")
    bouton_lancer.setFixedHeight(45)
    bouton_lancer.setEnabled(False)
    bouton_lancer.setStyleSheet("""QPushButton { font-size: 14px; background-color: #27AE60; color: white; border-radius: 8px; } QPushButton:hover { background-color: #1E8449; } QPushButton:disabled { background-color: #aaa; }""")
    bouton_lancer.clicked.connect(lancer_analyse_fichiers)

    bouton_charger = QPushButton("📂  Load imzML file(s)")
    bouton_charger.setFixedHeight(45)
    bouton_charger.setStyleSheet("""QPushButton { font-size: 14px; background-color: #4A90D9; color: white; border-radius: 8px; } QPushButton:hover { background-color: #357ABD; }""")
    bouton_charger.clicked.connect(ouvrir_fichiers)

    disposition_principale.addWidget(bouton_charger)
    disposition_principale.addSpacing(2)

    if mode == "classification":
        bouton_charger_pkl = QPushButton("🧪  Load pkl file")
        bouton_charger_pkl.setFixedHeight(45)
        bouton_charger_pkl.setStyleSheet("""QPushButton { font-size: 14px; background-color: #663399; color: white; border-radius: 8px; } QPushButton:hover { background-color: #6633cc; }""")
        bouton_charger_pkl.clicked.connect(ouvrir_fichiers_pkl)
        disposition_principale.addWidget(bouton_charger_pkl)
        disposition_principale.addSpacing(2)

    disposition_principale.addWidget(bouton_lancer)
    disposition_principale.addStretch()

    fenetre_chargement.show()

bouton_segmentation = QPushButton("📊  Segmentation")
bouton_segmentation.setFixedHeight(45)
bouton_segmentation.setStyleSheet("""QPushButton { font-size: 14px; background-color: #4A90D9; color: white; border-radius: 8px; } QPushButton:hover { background-color: #357ABD; }""")
bouton_segmentation.clicked.connect(lambda: ouvrir_fenetre_chargement("segmentation"))

bouton_classification = QPushButton("🧪  Classification")
bouton_classification.setFixedHeight(45)
bouton_classification.setStyleSheet("""QPushButton { font-size: 14px; background-color: #663399; color: white; border-radius: 8px; } QPushButton:hover { background-color: #6633cc; }""")
bouton_classification.clicked.connect(lambda: ouvrir_fenetre_chargement("classification"))

disposition_choix.addWidget(bouton_segmentation)
disposition_choix.addSpacing(2)
disposition_choix.addWidget(bouton_classification)
disposition_choix.addStretch()

sys.exit(application.exec_())