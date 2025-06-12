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
import csv
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

def extract_availability_dates(card, wait):
    try:
        all_dates = []  # Tableau pour accumuler toutes les disponibilités

        while True:
            # Attendre un court instant pour que le JavaScript rende les données
            time.sleep(1)

            # Récupérer les disponibilités actuelles
            try:
                availability_dates = card.find_elements(By.CSS_SELECTOR, "div[data-test-id='availabilities-container'] span")
                current_dates = [date.text for date in availability_dates if date.text]
                all_dates.extend(current_dates)  # Ajouter les disponibilités au tableau
                print(f"Disponibilités trouvées : {current_dates}")
            except Exception:
                print("Aucune disponibilité trouvée pour cette semaine.")

            # Vérifier si le bouton "Prochaines disponibilités" est présent et cliquable
            try:
                next_button = card.find_element(By.CSS_SELECTOR, "button[aria-label*='Prochaines disponibilités']")
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Prochaines disponibilités']")))
                next_button.click()
                print("Bouton 'Prochaines disponibilités' cliqué.")
            except Exception:
                print("Aucun bouton 'Prochaines disponibilités' trouvé. Fin de la navigation.")
                break

        return clean_availability_dates(all_dates)
    except Exception as e:
        print(f"Erreur lors de l'extraction des disponibilités : {e}")
        return []

def clean_availability_dates(raw_dates):
    today = datetime.now()
    current_year = today.year
    cleaned_dates = []

    # Gestion de la transition entre yyyy et yyyy+1
    previous_month = None

    for i in range(len(raw_dates)):
        try:
            # Exclure les créneaux horaires et autres textes
            if "—" not in raw_dates[i] and "Prochain RDV" not in raw_dates[i] and "Voir plus de créneaux" not in raw_dates[i]:
                if raw_dates[i].isdigit() or any(month in raw_dates[i] for month in ["janv.", "févr.", "mars", "avril", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]):
                    # Convertir la date en objet datetime
                    date_str = raw_dates[i]
                    if " " in date_str: 
                        day, month = date_str.split(" ")
                        month_mapping = {
                            "janv.": 1, "févr.": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                            "juil.": 7, "août": 8, "sept.": 9, "oct.": 10, "nov.": 11, "déc.": 12
                        }
                        month = month_mapping[month]

                        if previous_month and previous_month == 12 and month == 1:
                            current_year += 1

                        previous_month = month

                        date_obj = datetime(year=current_year, month=month, day=int(day))
                        cleaned_dates.append(date_obj)
                    else:
                        # Ignorer les éléments qui ne sont pas des dates valides
                        pass
                elif ":" in raw_dates[i]:  # Format "08:30"
                    if cleaned_dates:
                        last_date = cleaned_dates[-1]
                        hour, minute = map(int, raw_dates[i].split(":"))
                        cleaned_dates[-1] = last_date.replace(hour=hour, minute=minute)
                    else:
                        pass
        except ValueError:
            pass

    cleaned_dates = [date for date in cleaned_dates if date.hour != 0 or date.minute != 0]

    return cleaned_dates

def extract_card_data(card):
    try:
        try:
            name = card.find_element(By.CSS_SELECTOR, "h2").text
        except Exception:
            name = None

        print(f"Extraction des données pour le praticien : {name}")
        try:
            # availability = card.find_element(By.CSS_SELECTOR, "div[data-test-id='availabilities-container']").text
            availability = extract_availability_dates(card, WebDriverWait(card, 5))
        except Exception:
            availability = None

        try:
            video_icon = card.find_element(By.CSS_SELECTOR, "svg[data-icon-name='solid/video']")
            consultation_type = "visio"
        except Exception:
            consultation_type = "sur place"

        try:
            insurance_paragraphs = card.find_elements(By.CSS_SELECTOR, "p[data-design-system-component='Paragraph']")
            if insurance_paragraphs:
                # Prendre le dernier paragraphe
                insurance_paragraph = insurance_paragraphs[-1].text
                if "secteur 1" in insurance_paragraph.lower():
                    insurance_sector = "secteur 1"
                elif "secteur 2" in insurance_paragraph.lower():
                    insurance_sector = "secteur 2"
                else:
                    insurance_sector = "non conventionné"
            else:
                insurance_sector = "non conventionné"
        except Exception:
            insurance_sector = "non conventionné"

        try:
            address = card.find_element(By.CSS_SELECTOR, "div.flex.flex-wrap.gap-x-4").text
        except Exception:
            address = None

        with open("result.txt", "a", encoding="utf-8") as file:
            file.write(f"Nom : {name}\n")
            file.write(f"Prochaine disponibilité : {availability}\n")
            file.write(f"Type de consultation : {consultation_type}\n")
            file.write(f"Secteur d'assurance : {insurance_sector}\n")
            file.write(f"Adresse complète : {address}\n")
            file.write("-" * 50 + "\n")

        return {
            "name": name,
            "availability": availability,
            "consultation_type": consultation_type,
            "insurance_sector": insurance_sector,
            "address": address
        }
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
    print(f"Recherche de la spécialité médicale : {args.medical_query}")
    print(f"Recherche de l'adresse : {args.address_filter}")
    search_medical_query_and_adress(driver, wait, args.medical_query, args.address_filter)
        
    # Recuperation des résultats
    try:
        time.sleep(5)
        practitioner_cards = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dl-card-content"))
        )
        print(f"Nombre de praticiens trouvés : {len(practitioner_cards)}")
        practitioners_data = []
        index = 0
        for card in practitioner_cards[1:args.max_results + 1]:
            index += 1
            print(f"\nExtraction des données du praticien {index}/{args.max_results}")
            practitioners_data.append(extract_card_data(card))
    except Exception as e:
        print(f"Erreur lors de la recherche des divs : {e}")

    # Filtrer les résultats
    practitioners_data = filtres(practitioners_data, args)
    print(f"Nombre de praticiens après filtrage : {len(practitioners_data)}")

    driver.quit()

def filtered_practitioners_to_csv(practitioners_data):
    filename = "filtered_practitioners.csv"
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Availability", "Consultation Type", "Insurance Sector", "Address"])
        for practitioner in practitioners_data:
            writer.writerow([
                practitioner["name"],
                ", ".join([date.strftime("%d/%m/%Y %H:%M") for date in practitioner["availability"]]) if practitioner["availability"] else "N/A",
                practitioner["consultation_type"],
                practitioner["insurance_sector"],
                practitioner["address"]
            ])
    print(f"Les résultats filtrés ont été enregistrés dans {filename}")

def filtres(practitioners_data, args):
    # Filtrer les résultats selon les critères
    filtered_data = []
    for practitioner in practitioners_data:
        if practitioner["insurance_sector"] == args.insurance_type and \
           practitioner["consultation_type"] == args.consultation_type and \
           practitioner["availability"] and \
           practitioner["availability"][0] >= datetime.strptime(args.start_date, "%d/%m/%Y") and \
           practitioner["availability"][0] <= datetime.strptime(args.end_date, "%d/%m/%Y"):
            filtered_data.append(practitioner)

    # Exclure les zones spécifiées
    if args.exclude_zones:
        filtered_data = [p for p in filtered_data if not any(zone in p["address"] for zone in args.exclude_zones)]

    return filtered_data

if __name__ == "__main__":
    main()