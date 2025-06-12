python doctolib.py --max-results 10 --start-date 01/06/2025 --end-date 30/06/2025 \
--medical-query dermatologue --insurance-type secteur 1 --consultation-type sur place \
--price-range 50-150 --address-filter "75015" --exclude-zones "Boulogne"

python doctolib.py --medical-query "Dermatologue" --address-filter "30220"

Pour chaque praticien, extraire les données suivantes :
Nom complet
Prochaine disponibilité
Type de consultation : vidéo ou sur place
Secteur d’assurance (1, 2, ou non conventionné)
Selenium TP 1
Prix estimé de la consultation (si disponible)
Adresse complète :
Rue (ex. "12 Rue de Paris")
Code postal (ex. "75001")
Ville (ex. "Paris")