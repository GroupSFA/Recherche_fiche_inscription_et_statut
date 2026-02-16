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

# =====================================================
# CONFIG PAGE
# =====================================================
st.set_page_config(
    page_title="Vérification des statuts",
    page_icon="🎓",
    layout="wide"
)

# =====================================================
# CSS PRO (NO SCROLL + FULL SCREEN)
# =====================================================
st.markdown("""
<style>

html, body, .stApp {
    height:100vh;
    overflow:hidden;
    background:#0B1A2F;
    color:white;
}

.main .block-container{
    padding-top:0rem !important;
    padding-bottom:0rem !important;
    max-width:100%;
}

footer, header {visibility:hidden;}

.main-title{
    text-align:center;
    font-size:42px;
    font-weight:800;
    margin:10px 0;
}

.dashboard{
    height:calc(100vh - 70px);
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION STATE
# =====================================================
if "mode" not in st.session_state:
    st.session_state.mode = "selection"

# =====================================================
# LOAD FILE
# =====================================================
files = ["ABS_GENERAL.xlsx","ABS_GENERAL.csv","ABS_GENERAL.txt"]
file_found = next((f for f in files if os.path.exists(f)), None)

if not file_found:
    st.error("ABS_GENERAL introuvable")
    st.stop()

if file_found.endswith(".xlsx"):
    df = pd.read_excel(file_found)
elif file_found.endswith(".csv"):
    df = pd.read_csv(file_found)
else:
    df = pd.read_csv(file_found, delimiter="\t")

if "MATRICULE" not in df.columns:
    st.error("Colonne MATRICULE absente")
    st.stop()

# =====================================================
# TITRE (DESTROY LOGIQUE)
# =====================================================
if st.session_state.mode == "selection":
    st.markdown("""
    <div class="main-title">
    🎓 VÉRIFICATION DES STATUTS D'INSCRIPTION<br>
    <span style="font-size:22px;color:#B0C4DE">
    AFFECTÉ(E) / NON AFFECTÉ(E) 2025-2026
    </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div style='text-align:center;color:#B0C4DE'>✅ {len(df)} matricules chargés</div>",
        unsafe_allow_html=True
    )

# =====================================================
# INTERVALLE (TOUJOURS EN HAUT)
# =====================================================
c1,c2,c3,c4 = st.columns([1,1,1,1.5])

with c1:
    start_row = st.number_input("",1,len(df),1,label_visibility="collapsed")

with c2:
    end_row = st.number_input("",start_row,len(df),len(df),label_visibility="collapsed")

with c3:
    st.metric("À traiter", end_row-start_row+1)

with c4:
    launch = st.button("🔍 RECHERCHER",use_container_width=True)

if launch:
    st.session_state.mode="run"
    st.session_state.start=start_row
    st.session_state.end=end_row
    st.rerun()

# =====================================================
# ================= MODE RUN ==========================
# =====================================================
if st.session_state.mode=="run":

    matricules=df.iloc[
        st.session_state.start-1:st.session_state.end
    ]["MATRICULE"].astype(str).tolist()

    col_left,col_right=st.columns([2,1],gap="small")

    # LEFT : SCREENSHOT
    with col_left:
        screenshot_placeholder=st.empty()

    # RIGHT : STATS
    with col_right:
        progress_bar=st.progress(0)
        status_txt=st.empty()

        s1=st.empty()
        s2=st.empty()
        s3=st.empty()
        s4=st.empty()

    # COUNTERS
    aff=non_aff=intr=err=0
    results=[]

    # =================================================
    # SELENIUM PRO CONFIG
    # =================================================
    options=Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    service=Service("/usr/local/bin/chromedriver")
    driver=webdriver.Chrome(service=service,options=options)
    wait=WebDriverWait(driver,15)

    try:
        for i,matricule in enumerate(matricules):

            status_txt.markdown(
                f"**{i+1}/{len(matricules)} — Matricule : {matricule}**"
            )

            driver.get(
                "https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/"
            )

            champ=wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,"input[type='text']")
                )
            )

            champ.clear()
            champ.send_keys(matricule)
            champ.send_keys(Keys.RETURN)

            time.sleep(2)

            # SCREENSHOT
            screenshot_placeholder.image(
                driver.get_screenshot_as_png(),
                use_container_width=True
            )

            text=driver.page_source.lower()

            if "non affecte" in text:
                statut="NON AFFECTÉ"; non_aff+=1
            elif "affecte" in text:
                statut="AFFECTÉ"; aff+=1
            elif "introuvable" in text:
                statut="INTROUVABLE"; intr+=1
            else:
                statut="ERREUR"; err+=1

            results.append({
                "Matricule":matricule,
                "Statut":statut,
                "Date":datetime.now()
            })

            # UPDATE STATS LIVE
            s1.metric("✅ Affectés",aff)
            s2.metric("💻 Non affectés",non_aff)
            s3.metric("❓ Introuvables",intr)
            s4.metric("⚠️ Erreurs",err)

            progress_bar.progress((i+1)/len(matricules))

            driver.delete_all_cookies()

    finally:
        driver.quit()

    st.success("✅ TERMINÉ")

    st.dataframe(
        pd.DataFrame(results),
        use_container_width=True,
        hide_index=True
    )
