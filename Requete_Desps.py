import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
from datetime import datetime
import os
import random

def verification_bepc_complete():
    """
    Vérification complète de tous les matricules BEPC (1697 lignes)
    """
    
    # Charger vos données
    print("🔄 Chargement des données...")
    try:
        df = pd.read_excel("C:/Users/LeghoJoshua/Documents/ABS_GENERAL.xls")
        print(f"✅ Données chargées: {len(df)} lignes")
        print(f"📋 Colonnes: {list(df.columns)}")
        
        # Vérifier s'il y a un fichier de sauvegarde pour reprendre
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fichier_resultats = f"resultats_bepc_complet_{timestamp}.csv"
        fichier_checkpoint = f"checkpoint_bepc_{timestamp}.csv"
        
        # Utiliser tous les matricules
        matricules_complets = df['MATRICULE'].astype(str).tolist()
        print(f"🎯 Traitement de {len(matricules_complets)} matricules")
        
        # Variables pour le suivi
        start_index = 0
        resultats_existants = []
        
        # Vérifier s'il existe un fichier de checkpoint récent
        checkpoints = [f for f in os.listdir('.') if f.startswith('checkpoint_bepc_') and f.endswith('.csv')]
        if checkpoints:
            derniers_checkpoints = sorted(checkpoints, reverse=True)[:3]  # Les 3 plus récents
            print(f"📂 Checkpoints trouvés: {derniers_checkpoints}")
            
            # Demander si on veut reprendre (simulation - en réalité vous pourriez ajouter input())
            # Pour l'automatisation, on peut reprendre automatiquement le plus récent
            try:
                df_checkpoint = pd.read_csv(derniers_checkpoints[0])
                resultats_existants = df_checkpoint.to_dict('records')
                start_index = len(resultats_existants)
                print(f"🔄 Reprise depuis l'index {start_index}")
            except:
                print("⚠️ Impossible de charger le checkpoint, démarrage depuis le début")
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return

    # Configuration Chrome optimisée pour un traitement long
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Économiser de la bande passante
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Variables pour les statistiques
    compteurs = {
        'AFFECTE': 0,
        'NON_AFFECTE': 0,
        'ADMIS': 0,
        'REFUSE': 0,
        'ECHEC': 0,
        'AJOURNE': 0,
        'INTROUVABLE': 0,
        'ERREUR': 0,
        'INDETERMINE': 0,
        'AUTRE': 0
    }
    
    resultats = resultats_existants.copy()
    
    try:
        # Initialiser le driver Chrome
        print(f"\n🌐 Initialisation du navigateur...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(1920, 1080)
        
        # Boucle principale pour tous les matricules
        for i in range(start_index, len(matricules_complets)):
            matricule = matricules_complets[i]
            position = i + 1
            
            print(f"\n{'='*60}")
            print(f"🔄 TRAITEMENT {position}/{len(matricules_complets)}: Matricule {matricule}")
            print(f"⏱️ Progression: {(position/len(matricules_complets)*100):.1f}%")
            print(f"{'='*60}")
            
            try:
                # Gestion des pauses adaptatives
                if position % 50 == 0:  # Pause longue tous les 50
                    pause_longue = random.randint(30, 60)
                    print(f"⏸️ Pause longue de {pause_longue}s (position {position})")
                    time.sleep(pause_longue)
                elif position % 10 == 0:  # Pause moyenne tous les 10
                    pause_moyenne = random.randint(10, 20)
                    print(f"⏸️ Pause moyenne de {pause_moyenne}s")
                    time.sleep(pause_moyenne)
                
                # Charger la page avec retry
                max_retries = 3
                page_loaded = False
                
                for attempt in range(max_retries):
                    try:
                        print(f"🌍 Tentative {attempt + 1}: Chargement de la page...")
                        driver.get("https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/")
                        
                        WebDriverWait(driver, 15).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        
                        page_loaded = True
                        break
                        
                    except Exception as e:
                        print(f"⚠️ Échec tentative {attempt + 1}: {str(e)[:100]}")
                        if attempt < max_retries - 1:
                            time.sleep(5)
                        continue
                
                if not page_loaded:
                    print("❌ Impossible de charger la page")
                    resultats.append({
                        'matricule': matricule,
                        'statut': 'ERREUR',
                        'niveau': 'NON_DEFINI',
                        'details': 'Page non accessible',
                        'position': position
                    })
                    compteurs['ERREUR'] += 1
                    continue
                
                # Attendre le chargement JavaScript
                time.sleep(random.uniform(2, 4))
                
                # Recherche du champ de saisie
                print("🔍 Recherche du champ de saisie...")
                champ_trouve = False
                champ = None
                
                selectors_a_tester = [
                    ("input[name='matricule']", By.CSS_SELECTOR),
                    ("input[placeholder*='Votre matricule' i]", By.CSS_SELECTOR),
                    ("input[type='text']", By.CSS_SELECTOR),
                    ("#matricule", By.CSS_SELECTOR),
                    ("//input[contains(@placeholder, 'Votre matricule')]", By.XPATH),
                    ("//input[@type='text']", By.XPATH),
                ]
                
                for selector, by_method in selectors_a_tester:
                    try:
                        champ = WebDriverWait(driver, 8).until(
                            EC.presence_of_element_located((by_method, selector))
                        )
                        
                        if champ.is_displayed() and champ.is_enabled():
                            print(f"✅ Champ trouvé: {selector}")
                            champ_trouve = True
                            break
                            
                    except Exception:
                        continue
                
                if not champ_trouve or champ is None:
                    print("❌ Champ de saisie non trouvé")
                    resultats.append({
                        'matricule': matricule,
                        'statut': 'ERREUR',
                        'niveau': 'NON_DEFINI',
                        'details': 'Champ de saisie non trouvé',
                        'position': position
                    })
                    compteurs['ERREUR'] += 1
                    continue
                
                # Saisir le matricule
                print(f"⌨️ Saisie du matricule: {matricule}")
                try:
                    driver.execute_script("arguments[0].click();", champ)
                    time.sleep(0.5)
                    champ.clear()
                    time.sleep(0.5)
                    
                    # Saisie progressive pour éviter la détection
                    for char in str(matricule):
                        champ.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                    
                except Exception as e:
                    print(f"❌ Erreur lors de la saisie: {e}")
                    resultats.append({
                        'matricule': matricule,
                        'statut': 'ERREUR',
                        'niveau': 'NON_DEFINI',
                        'details': f'Erreur saisie: {str(e)[:50]}',
                        'position': position
                    })
                    compteurs['ERREUR'] += 1
                    continue
                
                # Soumettre le formulaire
                print("📤 Soumission du formulaire...")
                bouton_trouve = False
                
                bouton_selectors = [
                    ("button[type='submit']", By.CSS_SELECTOR),
                    ("input[type='submit']", By.CSS_SELECTOR),
                    ("button", By.CSS_SELECTOR),
                    ("//button[contains(text(), 'Aperçu')]", By.XPATH),
                    ("//input[@type='submit']", By.XPATH),
                ]
                
                for selector, by_method in bouton_selectors:
                    try:
                        bouton = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((by_method, selector))
                        )
                        
                        try:
                            bouton.click()
                        except:
                            driver.execute_script("arguments[0].click();", bouton)
                        
                        bouton_trouve = True
                        break
                        
                    except Exception:
                        continue
                
                if not bouton_trouve:
                    try:
                        champ.send_keys(Keys.RETURN)
                    except:
                        print("❌ Impossible de soumettre")
                        continue
                
                # Attendre les résultats
                print("⏳ Attente des résultats...")
                time.sleep(random.uniform(6, 10))
                
                # Analyser la page résultat
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: len(d.page_source) > 5000
                    )
                except:
                    pass
                
                page_text = driver.page_source.lower()
                page_title = driver.title.lower()

                # Déterminer le statut en cherchant l'élément spécifique
                statut = 'INDETERMINE'
                details = 'Résultat non identifié'
                niveau = 'NON_DEFINI'

                try:
                    statut_element = driver.find_element(By.CSS_SELECTOR, 'b.textzone-subtitle4')
                    statut_text = statut_element.text.strip().upper()

                    if 'AFFECTE(E)' in statut_text and 'NON' not in statut_text:
                        statut = 'AFFECTE'
                        details = 'Candidat affecté(e)'
                    elif 'NON AFFECTE(E)' in statut_text:
                        statut = 'NON_AFFECTE'
                        details = 'Candidat non affecté(e)'
                    else:
                        statut = 'AUTRE'
                        details = f'Statut: {statut_text}'
                except:
                    # Si l'élément n'est pas trouvé, vérifier les cas d'erreur
                    if 'introuvable' in page_text or 'non trouvé' in page_text:
                        statut = 'INTROUVABLE'
                        details = 'Matricule non trouvé'
                    elif 'erreur' in page_text or 'error' in page_text:
                        statut = 'ERREUR'
                        details = 'Erreur système'
                
                # Récupérer le niveau de l'élève (deuxième élément)
                try:
                    niveau_elements = driver.find_elements(By.CSS_SELECTOR, 'b.textzone-subtitle-col-red')
                    if len(niveau_elements) >= 2:
                        niveau = niveau_elements[1].text.strip().upper()  # Deuxième élément (index 1)
                        print(f"📚 Niveau détecté: {niveau}")
                    else:
                        niveau = 'NON_DEFINI'
                        print(f"⚠️ Moins de 2 éléments trouvés ({len(niveau_elements)} trouvé(s))")
                except Exception as e:
                    niveau = 'NON_DEFINI'
                    print(f"⚠️ Niveau non trouvé: {e}")
                
                # Icônes pour l'affichage
                status_icons = {
                    'ADMIS': '✅', 'REFUSE': '❌', 'ECHEC': '❌',
                    'AJOURNE': '⚠️', 'INTROUVABLE': '❓',
                    'ERREUR': '🔥', 'INDETERMINE': '❔'
                }
                
                icon = status_icons.get(statut, '❔')
                print(f"{icon} Résultat: {statut} - {details}")
                
                resultats.append({
                    'matricule': matricule,
                    'statut': statut,
                    'niveau': niveau,
                    'details': details,
                    'position': position,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Incrémenter le compteur (avec sécurité)
                if statut in compteurs:
                    compteurs[statut] += 1
                else:
                    print(f"⚠️ Statut inconnu: {statut}")
                    compteurs['AUTRE'] += 1
                
                # SAUVEGARDE IMMÉDIATE après chaque résultat
                df_temp = pd.DataFrame(resultats)
                df_temp.to_csv(fichier_checkpoint, index=False, encoding='utf-8')
                print(f"💾 Résultat enregistré")
                
                # Statistiques périodiques (tous les 25 résultats)
                if position % 25 == 0:
                    print(f"📊 Statistiques (position {position}):")
                    for statut_key, count in compteurs.items():
                        if count > 0:
                            print(f"   {statut_key}: {count}")
                
                # Pause variable entre les requêtes
                pause_time = random.uniform(3, 8)
                if position % 100 == 0:  # Pause plus longue tous les 100
                    pause_time = random.uniform(15, 30)
                
                print(f"⏸️ Pause de {pause_time:.1f}s...")
                time.sleep(pause_time)
                
            except Exception as e:
                print(f"❌ Exception technique pour {matricule}: {e}")
                resultats.append({
                    'matricule': matricule,
                    'statut': 'ERREUR',
                    'niveau': 'NON_DEFINI',
                    'details': f'Exception: {str(e)[:100]}',
                    'position': position,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                compteurs['ERREUR'] += 1
                
                # Sauvegarder même en cas d'erreur
                df_temp = pd.DataFrame(resultats)
                df_temp.to_csv(fichier_checkpoint, index=False, encoding='utf-8')
                
                time.sleep(3)
        
        # Affichage des résultats finaux
        print("\n" + "="*80)
        print("🎉 RÉSULTATS FINAUX - VÉRIFICATION BEPC COMPLÈTE")
        print("="*80)
        
        total = len(resultats)
        print(f"📊 STATISTIQUES GLOBALES:")
        print(f"   Total traité: {total}")
        for statut_key, count in compteurs.items():
            pourcentage = (count/total*100) if total > 0 else 0
            if count > 0:
                icon = status_icons.get(statut_key, '❔')
                print(f"   {icon} {statut_key}: {count} ({pourcentage:.1f}%)")
        
        # Sauvegarde finale
        if resultats:
            df_resultats = pd.DataFrame(resultats)
            df_resultats.to_csv(fichier_resultats, index=False, encoding='utf-8')
            print(f"\n💾 Résultats finaux sauvés dans: {fichier_resultats}")
            
            # Nettoyer le fichier de checkpoint
            try:
                if os.path.exists(fichier_checkpoint):
                    os.remove(fichier_checkpoint)
                    print("🧹 Fichier checkpoint nettoyé")
            except:
                pass
        
        print(f"\n⏱️ Traitement terminé à: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        
        # Sauvegarde d'urgence
        if resultats:
            fichier_urgence = f"sauvegarde_urgence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            pd.DataFrame(resultats).to_csv(fichier_urgence, index=False, encoding='utf-8')
            print(f"🆘 Sauvegarde d'urgence: {fichier_urgence}")
        
    finally:
        # Fermer le navigateur proprement
        try:
            if 'driver' in locals():
                driver.quit()
                print("\n🔒 Navigateur fermé")
        except Exception as e:
            print(f"Erreur fermeture navigateur: {e}")

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DE LA VÉRIFICATION BEPC COMPLÈTE")
    print("📋 Traitement de 1697 matricules")
    print("⚠️ Ce processus peut prendre plusieurs heures")
    print("💾 Sauvegardes automatiques tous les 25 résultats")
    print("-" * 60)
    
    verification_bepc_complete()
    print("\n✅ VÉRIFICATION COMPLÈTE TERMINÉE!")