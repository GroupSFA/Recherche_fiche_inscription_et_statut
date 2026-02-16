import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import os

# ==========================
# CONFIG PAGE
# ==========================
st.set_page_config(
    page_title="Vérification des statuts",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================
# STYLE GLOBAL - BLEU NUIT
# ==========================
st.markdown("""
<style>
    /* Fond bleu nuit */
    .stApp {
        background-color: #0B1A2F;
    }
    
    html, body, [class*="css"] {
        background-color: #0B1A2F;
        color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    
    /* Conteneur principal pleine largeur - SANS PADDING EN HAUT */
    .main .block-container {
        max-width: 100%;
        padding: 0rem 2rem 0rem 2rem !important;
        background-color: #0B1A2F;
    }
    
    /* Supprimer tous les margin-top et padding-top inutiles */
    .main > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Titre centré - visible uniquement au début */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: white;
        margin-top: 5px;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 1px;
        padding: 10px;
        border-bottom: 2px solid #1E3A5F;
    }
    
    /* Style des métriques */
    [data-testid="stMetric"] {
        background-color: #1E3A5F;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #2C4F7C;
        margin: 2px 0;
    }
    
    [data-testid="stMetricLabel"] {
        color: #B0C4DE;
        font-size: 12px;
    }
    
    [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    
    /* Style des inputs - PLUS COMPACTS */
    .stNumberInput input {
        background-color: #1E3A5F;
        color: white;
        border: 1px solid #2C4F7C;
        border-radius: 5px;
        padding: 2px 5px !important;
        height: 35px !important;
    }
    
    .stNumberInput label {
        color: #B0C4DE !important;
        font-size: 14px !important;
    }
    
    /* Style du bouton */
    .stButton button {
        background-color: #1E3A5F;
        color: white;
        border: 2px solid #2C4F7C;
        border-radius: 8px;
        padding: 5px 15px;
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        height: 45px;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #2C4F7C;
        border-color: #3A6A9F;
    }
    
    /* Zone des captures - PLEINE HAUTEUR */
    .screenshot-container {
        border: 2px solid #1E3A5F;
        border-radius: 10px;
        overflow: hidden;
        margin: 0;
        background-color: #0F1F35;
        height: calc(100vh - 120px);  /* Hauteur adaptée à l'écran */
        display: flex;
        flex-direction: column;
    }
    
    /* Style des progressions - PLEINE HAUTEUR */
    .progress-container {
        background-color: #0F1F35;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #1E3A5F;
        margin: 0;
        height: calc(100vh - 120px);  /* Hauteur adaptée à l'écran */
        overflow-y: auto;  /* Scroll interne si nécessaire */
    }
    
    /* Barre de progression */
    .stProgress > div > div > div > div {
        background-color: #2E8B57 !important;
    }
    
    /* Style des dataframes */
    .dataframe-container {
        background-color: #0F1F35;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #1E3A5F;
        margin-top: 10px;
    }
    
    /* Images en plein écran */
    [data-testid="stImage"] {
        width: 100%;
        margin: 0;
        padding: 0;
        flex: 1;
    }
    
    [data-testid="stImage"] img {
        width: 100%;
        height: 100%;
        object-fit: contain;  /* Ajuste l'image sans déformation */
        border-radius: 8px;
        border: 2px solid #1E3A5F;
    }
    
    /* Texte d'information */
    .info-text {
        color: #B0C4DE;
        font-size: 14px;
        text-align: center;
        margin: 5px 0;
    }
    
    /* Ligne de séparation - invisible */
    hr {
        border-color: #1E3A5F;
        margin: 5px 0;
    }
    
    /* Messages de succès/erreur */
    .stAlert {
        background-color: #1E3A5F !important;
        color: white !important;
        border: 1px solid #2C4F7C !important;
        font-size: 12px !important;
        padding: 5px !important;
    }
    
    /* Titre de colonnes pour l'intervalle - TRÈS COMPACT */
    .interval-title {
        color: #B0C4DE;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 2px;
        margin-top: 0;
    }
    
    /* Cache les éléments inutiles */
    footer {display: none;}
    header {display: none;}
    
    /* Supprimer les espaces blancs en haut */
    .stApp > header {
        display: none !important;
    }
    
    /* Ajustement des colonnes */
    div[data-testid="column"] {
        padding: 0 2px;
    }
    
    /* Style du total */
    .total-container {
        background-color: #1E3A5F;
        padding: 5px;
        border-radius: 5px;
        text-align: center;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Masquer le titre quand la recherche est lancée */
    .hidden-title {
        display: none !important;
    }
    
    /* Zone de sélection compacte */
    .selection-zone {
        margin-bottom: 5px;
    }
    
    /* Pour que tout tienne sur une seule page */
    .main > div:first-child {
        min-height: auto !important;
    }
    
</style>
""", unsafe_allow_html=True)

# ==========================
# CHARGEMENT FICHIER
# ==========================
try:
    # Recherche du fichier avec différents formats
    fichiers_possibles = ["ABS_GENERAL.xlsx", "ABS_GENERAL.csv", "ABS_GENERAL.txt"]
    fichier_trouve = None
    
    for fichier in fichiers_possibles:
        if os.path.exists(fichier):
            fichier_trouve = fichier
            break
    
    if fichier_trouve is None:
        st.error("❌ Aucun fichier ABS_GENERAL trouvé (xlsx, csv ou txt)")
        st.stop()
    
    # Chargement selon l'extension
    if fichier_trouve.endswith('.xlsx'):
        df = pd.read_excel(fichier_trouve, engine="openpyxl")
    elif fichier_trouve.endswith('.csv'):
        df = pd.read_csv(fichier_trouve)
    else:
        df = pd.read_csv(fichier_trouve, delimiter='\t')  # Pour les txt

except Exception as e:
    st.error(f"❌ Erreur chargement : {e}")
    st.stop()

if "MATRICULE" not in df.columns:
    st.error("❌ Colonne MATRICULE absente dans le fichier.")
    st.stop()

# ==========================
# INITIALISATION SESSION STATE
# ==========================
if 'verification_lancee' not in st.session_state:
    st.session_state.verification_lancee = False

# ==========================
# TITRE CENTRÉ (CACHÉ APRÈS LANCEMENT)
# ==========================
if not st.session_state.verification_lancee:
    st.markdown("""
    <div class="main-title">
        🎓 VÉRIFICATION DES STATUTS D'INSCRIPTION<br>
        <span style="font-size: 24px; color: #B0C4DE;">AFFECTÉ(E) / NON AFFECTÉ(E) 2025-2026</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div class='info-text'>✅ {len(df)} matricules chargés depuis la table scolaire à traiter</div>", unsafe_allow_html=True)

# ==========================
# SÉLECTION DE L'INTERVALLE (TOUJOURS EN HAUT)
# ==========================
st.markdown('<div class="selection-zone">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])

with col1:
    st.markdown('<div class="interval-title">📌 DÉPART</div>', unsafe_allow_html=True)
    start_row = st.number_input(
        "",
        min_value=1,
        max_value=len(df),
        value=1,
        key="start",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="interval-title">🏁 FIN</div>', unsafe_allow_html=True)
    end_row = st.number_input(
        "",
        min_value=start_row,
        max_value=len(df),
        value=len(df),
        key="end",
        label_visibility="collapsed"
    )

with col3:
    st.markdown('<div class="interval-title">📊 TRAITER</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="total-container">
        <span style="font-size: 20px; font-weight: 700;">{end_row - start_row + 1}</span>
        <span style="color: #B0C4DE; font-size: 14px;"> / {len(df)}</span>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown('<div class="interval-title"> </div>', unsafe_allow_html=True)  # Espace pour aligner
    bouton_lancement = st.button("🔍 RECHERCHER", use_container_width=True)

if start_row > end_row:
    st.error("❌ La ligne de fin doit être ≥ à la ligne de début")
    st.stop()

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")

# ==========================
# BOUTON LANCEMENT
# ==========================
if bouton_lancement:
    st.session_state.verification_lancee = True
    
    # Sélection des matricules selon l'intervalle choisi
    matricules = df.iloc[start_row-1:end_row]["MATRICULE"].astype(str).tolist()
    
    # CRÉATION DES COLONNES : 2/3 GAUCHE (CAPTURES) - 1/3 DROITE (PROGRESSIONS)
    col_captures, col_progress = st.columns([2, 1])
    
    with col_captures:
        with st.container():
            st.markdown('<div class="screenshot-container">', unsafe_allow_html=True)
            screenshot_placeholder = st.empty()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col_progress:
        with st.container():
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)
            
            # Barre de progression
            st.markdown("### 📊 PROGRESSION")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Statistiques en temps réel
            st.markdown("### 📈 STATISTIQUES")
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                stat_affecte = st.empty()
                stat_introuvable = st.empty()
            
            with col_stat2:
                stat_non_affecte = st.empty()
                stat_erreur = st.empty()
            
            # Informations supplémentaires
            st.markdown("### ℹ️ INFOS")
            info_container = st.empty()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialisation des compteurs
    count_affecte = 0
    count_non_affecte = 0
    count_introuvable = 0
    count_erreur = 0
    resultats = []
    driver = None
    
    try:
        # Configuration Chrome optimisée
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        
        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Boucle de traitement
        for i, matricule in enumerate(matricules):
            # Mise à jour des infos
            status_text.markdown(f"""
            **Matricule :** {matricule}  
            **Ligne :** {start_row + i}/{end_row}  
            **Progression :** {i+1}/{len(matricules)}
            """)
            
            # Navigation
            driver.get("https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/")
            
            # Recherche
            wait = WebDriverWait(driver, 15)
            champ = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            champ.clear()
            champ.send_keys(str(matricule))
            champ.send_keys(Keys.RETURN)
            
            time.sleep(2)
            
            # 🖥 Capture d'écran
            png = driver.get_screenshot_as_png()
            screenshot_placeholder.image(png, use_container_width=True)
            
            # Analyse du résultat
            page_text = driver.page_source.lower()
            
            if "non affecte" in page_text:
                statut = "NON AFFECTÉ"
                count_non_affecte += 1
            elif "affecte" in page_text:
                statut = "AFFECTÉ"
                count_affecte += 1
            elif "introuvable" in page_text:
                statut = "INTROUVABLE"
                count_introuvable += 1
            else:
                statut = "ERREUR"
                count_erreur += 1
            
            # Enregistrement
            resultats.append({
                "Matricule": matricule,
                "Statut": statut,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 📊 Mise à jour stats
            stat_affecte.metric("✅ AFFECTÉS", count_affecte)
            stat_non_affecte.metric("💻 NON AFFECTÉS", count_non_affecte)
            stat_introuvable.metric("❓ INTROUVABLES", count_introuvable)
            stat_erreur.metric("⚠️ ERREURS", count_erreur)
            
            # Info supplémentaire
            info_container.info(f"💾 RAM: {i+1}/{len(matricules)}")
            
            # Barre de progression
            progress_bar.progress((i + 1) / len(matricules))
            
            # 🧠 Optimisation RAM
            driver.delete_all_cookies()
            
            if i < len(matricules) - 1:
                time.sleep(1)
        
        # FIN DU TRAITEMENT
        with col_progress:
            st.success("✅ TERMINÉ")
            
            # Résumé final
            total = len(matricules)
            st.markdown(f"""
            **RÉSUMÉ**  
            ✅ {count_affecte} ({count_affecte/total*100:.1f}%)  
            💻 {count_non_affecte} ({count_non_affecte/total*100:.1f}%)  
            ❓ {count_introuvable} ({count_introuvable/total*100:.1f}%)  
            ⚠️ {count_erreur} ({count_erreur/total*100:.1f}%)
            """)
        
        # Affichage des résultats
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.markdown("### 📋 RÉSULTATS")
        df_resultats = pd.DataFrame(resultats)
        st.dataframe(df_resultats, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
    
    finally:
        if driver:
            driver.quit()

else:
    if not st.session_state.verification_lancee:
        # Message d'instruction
        st.markdown("""
        <div style="text-align: center; padding: 30px; background-color: #0F1F35; border-radius: 10px; border: 1px solid #1E3A5F;">
            <h3 style="color: white;">👆 CLIQUEZ SUR RECHERCHER POUR COMMENCER</h3>
            <p style="color: #B0C4DE;">Ligne {} à {} ({} matricules sur {})</p>
            <p style="color: #B0C4DE; font-size: 13px;">Captures: 2/3 gauche | Stats: 1/3 droite</p>
        </div>
        """.format(start_row, end_row, end_row - start_row + 1, len(df)), unsafe_allow_html=True)