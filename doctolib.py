import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
from datetime import datetime
DOCTOLIB = "https://www.doctolib.fr/"

today = datetime.now()

def main():
    parser = argparse.ArgumentParser(
        description="Recherche de médecins sur Doctolib avec des filtres personnalisés."
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Nombre maximum de résultats à afficher (ex : 10 premiers médecins)."
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=today.strftime("%d/%m/%Y"),
        help="Date de début de la période de disponibilité (format JJ/MM/AAAA)."
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=(today.replace(day=today.day + 7)).strftime("%d/%m/%Y"),
        help="Date de fin de la période de disponibilité (format JJ/MM/AAAA)."
    )
    parser.add_argument(
        "--medical-query",
        type=str,
        default="généraliste",
        help="Requête médicale (ex : 'dermatologue', 'généraliste')."
    )
    parser.add_argument(
        "--insurance-type",
        type=str,
        choices=["secteur 1", "secteur 2", "non conventionné"],
        default="secteur 1",
        help="Type d’assurance : secteur 1, secteur 2, non conventionné."
    )
    parser.add_argument(
        "--consultation-type",
        type=str,
        choices=["visio", "sur place"],
        default="sur place",
        help="Type de consultation : en visio ou sur place."
    )
    parser.add_argument(
        "--price-range",
        type=str,
        default="0-100",
        help="Plage de prix : minimum et maximum (en €), format 'min-max'."
    )
    parser.add_argument(
        "--address-filter",
        type=str,
        required=False,
        default="Autour de moi",
        help="Mot-clé libre dans l’adresse (ex: 'rue de Vaugirard', '75015', 'Boulogne')."
    )
    parser.add_argument(
        "--exclude-zones",
        type=str,
        nargs="*",
        required=False,
        help="Zones à exclure (ex : '75015', 'Boulogne')."
    )

    args = parser.parse_args()

    print("Paramètres de recherche :")
    print(f"Nombre maximum de résultats : {args.max_results}")
    print(f"Période de disponibilité : {args.start_date} à {args.end_date}")
    print(f"Requête médicale : {args.medical_query}")
    print(f"Type d’assurance : {args.insurance_type}")
    print(f"Type de consultation : {args.consultation_type}")
    print(f"Plage de prix : {args.price_range}")
    print(f"Filtre géographique : {args.address_filter}")
    print(f"Zones exclues : {args.exclude_zones}")

    scrap_doctolib(args)

def search_medical_query_and_adress(driver, wait, medical_query, address_filter):
    # Rechercher la spécialité médicale
    if medical_query:
        try:
            print("Recherche de la spécialité médicale :", medical_query)
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-query-input"))
            )
            search_input.clear()
            search_input.send_keys(medical_query)
            
            first_result = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "ul#search-query-input-results-container li button"))
            )
            first_result.click()
        except Exception as e:
            print(f"Error while searching for medical specialty: {e}")
    else:
        print("Aucune spécialité médicale spécifiée, recherche de tous les médecins.")
    
    # Recherche de la localisation
    if address_filter:
        try:
            print("Recherche de la localisation :", address_filter)
            place_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.searchbar-input.searchbar-place-input"))
            )
            
            if place_input.is_enabled() and place_input.is_displayed():
                place_input.click()
                place_input.clear()
                place_input.send_keys(address_filter)

                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul#search-place-input-results-container"))
                )

                second_result = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ul#search-place-input-results-container li:nth-child(2) button"))
                )

                second_result.click()
                print(f"Localisation '{address_filter}' sélectionnée.")
            else:
                print("Le champ de localisation n'est pas dans un état valide.")
        except Exception as e:
            print(f"Erreur lors de la recherche de la localisation : {e}")
    else:
        print("Aucune localisation spécifiée, recherche de tous les médecins.")

    # Cliquer sur le bouton "Rechercher" après avoir rempli les champs
    try:
        search_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.searchbar-submit-button"))
        )
        search_button.click()
        print("Bouton 'Rechercher' cliqué.")
    except Exception as e:
        print(f"Erreur lors du clic sur le bouton 'Rechercher' : {e}")

def extract_card_data(card):
    try:
        try:
            name = card.find_element(By.CSS_SELECTOR, "h2").text
        except Exception:
            name = None

        try:
            availability = card.find_element(By.CSS_SELECTOR, "div[data-test-id='availabilities-container']").text
        except Exception:
            availability = None

        try:
            consultation_type = card.find_element(By.CSS_SELECTOR, "p[data-design-system-component='Paragraph']").text
        except Exception:
            consultation_type = None

        try:
            insurance_sector = card.find_element(By.CSS_SELECTOR, "p[data-design-system-component='Paragraph']").text
        except Exception:
            insurance_sector = None

        try:
            address = card.find_element(By.CSS_SELECTOR, "div.flex.flex-wrap.gap-x-4").text
        except Exception:
            address = None

        print(f"Nom : {name}")
        print(f"Prochaine disponibilité : {availability}")
        print(f"Type de consultation : {consultation_type}")
        print(f"Secteur d'assurance : {insurance_sector}")
        print(f"Adresse complète : {address}")
        print("-" * 50)
    except Exception as e:
        print(f"Erreur lors de l'extraction des données pour un praticien : {e}")

def scrap_doctolib(args):
    # Lancement du navigateur
    driver = webdriver.Chrome()
    driver.get(DOCTOLIB)
    driver.implicitly_wait(5)
    wait = WebDriverWait(driver, 5)

    # Refuser les cookies
    try :
        reject_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-disagree-button"))
        )
        reject_btn.click()
        wait.until(EC.invisibility_of_element_located((By.ID, "didomi-notice-disagree-button")))
    except Exception as e:
        print(f"Error while rejecting cookies: {e}")

    # Rechercher la spécialité médicale et l'adresse
    search_medical_query_and_adress(driver, wait, args.medical_query, args.address_filter)
        
    # time.sleep(50)
    # Recuperation des résultats
    try:
        time.sleep(5)
        practitioner_cards = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dl-card-content"))
        )
        print(f"Nombre de praticiens trouvés : {len(practitioner_cards)}")
        for card in practitioner_cards[1:]:
            extract_card_data(card)
    except Exception as e:
        print(f"Erreur lors de la recherche des divs : {e}")

    driver.quit()


if __name__ == "__main__":
    main()