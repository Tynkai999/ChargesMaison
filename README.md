# Charges Maison

Application Django pour répartir automatiquement les charges d'une colocation
(loyer, électricité, eau, internet, etc.) entre les résidents, en tenant
compte de leur présence dans la maison et des contributions externes au wifi.

## Règles de répartition implémentées

- **Loyer** : le montant total est divisé par le **nombre total de résidents**
  actifs (présents ou absents). Tout le monde paie sa part de loyer.
- **Autres charges** (électricité, eau, ménage, etc.) : le total est divisé
  uniquement entre les résidents **présents** sur la période. Un résident
  absent ne paie que sa part de loyer.
- **Internet / Wifi** : on part du montant de l'abonnement, on soustrait la
  somme des contributions des **personnes externes** à la maison, et le reste
  est ajouté au pot des « autres charges » (donc réparti lui aussi entre les
  résidents présents).

Exemple : loyer 25 000 FCFA / 5 résidents = 5 000 FCFA chacun. Wifi 15 000 FCFA,
deux externes contribuent 2 000 FCFA chacun et un autre 1 000 FCFA (total
3 000 FCFA) : il reste 12 000 FCFA à ajouter aux charges des présents.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser     # compte administrateur de la maison
python manage.py seed_charge_types   # crée les types de charge de base
python manage.py runserver
```

Ouvrez ensuite http://127.0.0.1:8000/

- Interface utilisateur : http://127.0.0.1:8000/
- Interface d'administration Django (gestion avancée) : http://127.0.0.1:8000/admin/

## Prise en main

1. Connectez-vous avec le compte administrateur créé via `createsuperuser`.
2. Menu **Résidents → Créer un compte résident** : créez les 5 comptes
   (username + mot de passe) des personnes de la maison.
3. Menu **Types de charge** : la commande `seed_charge_types` a déjà créé
   Loyer, Électricité, Eau, Internet/Wifi et Ménage/Entretien. Vous pouvez en
   ajouter d'autres. Cochez bien « C'est le loyer » sur le type Loyer et
   « C'est l'abonnement wifi » sur le type Internet.
4. Menu **Contributeurs wifi** : ajoutez les personnes externes qui
   participent à l'abonnement internet (nom, téléphone).
5. Menu **Périodes → Nouvelle période** : créez le mois en cours (ex : Août
   2026), puis ouvrez son détail pour :
   - saisir le loyer, l'électricité, le wifi, etc. (montants du mois) ;
   - saisir les contributions des externes au wifi ;
   - cocher/décocher la présence de chaque résident ;
   - consulter la répartition calculée automatiquement en bas de page.

Chaque résident peut ensuite se connecter avec son propre compte et consulter
**Mes contributions** pour voir l'historique de ce qu'il doit payer, mois par
mois, sans avoir accès à la création de comptes (réservée aux
administrateurs).

## PDF et envoi individuel

Dans le détail d'une période :

- Chaque résident peut télécharger **son** reçu PDF (bouton téléchargement sur
  sa ligne). Il ne peut pas télécharger celui d'un autre résident.
- N'importe quel résident connecté peut télécharger le **récapitulatif PDF**
  de la période (tous les résidents), cohérent avec le tableau déjà visible à
  l'écran.
- L'administration (compte "staff" ou superutilisateur) peut en plus
  **envoyer** le reçu PDF de n'importe quel résident par email (bouton
  enveloppe). Cela nécessite que l'email du résident soit renseigné (champ
  ajouté au formulaire de création de résident, ou modifiable ensuite via
  `/admin/`).
- Par défaut, les emails s'affichent simplement dans la console où tourne
  `runserver` (pratique pour tester). Pour un envoi réel, configurez le
  backend SMTP dans `chargesmaison/settings.py` (voir les commentaires dans
  la section `EMAIL_BACKEND`).

## Suivi des paiements

Bouton **Suivi des paiements** (visible seulement par l'administration) dans
le détail d'une période : une page où l'on coche qui a payé, on saisit le
montant réellement versé, la date et une note. Le statut (Payé / Partiel /
Impayé) est calculé et affiché automatiquement, y compris directement dans le
tableau de répartition de la période et sur le reçu PDF de chaque résident.

## Déploiement en production

Ce projet est livré avec des réglages de développement (`DEBUG = True`,
base SQLite). Avant de le mettre en ligne pour un usage réel :

- changez `SECRET_KEY` dans `chargesmaison/settings.py` ;
- mettez `DEBUG = False` et renseignez `ALLOWED_HOSTS` ;
- envisagez PostgreSQL plutôt que SQLite si plusieurs personnes doivent
  écrire en même temps ;
- servez les fichiers statiques avec `collectstatic` + un serveur comme
  Nginx, ou un service tel que Render / Railway / PythonAnywhere.

## Structure du projet

```
chargesmaison/        Réglages du projet Django (settings, urls)
core/
  models.py            Resident, ExternalContributor, Period, ChargeType,
                        Charge, Presence, WifiContribution, Payment
  services.py           Logique de calcul de la répartition (compute_period_summary)
  pdf.py                 Génération des PDF (reçu individuel + récapitulatif) avec reportlab
  views.py, forms.py, urls.py, admin.py
  templates/core/       Toutes les pages HTML (Bootstrap 5), dont payment_tracking.html
  management/commands/  seed_charge_types
```
