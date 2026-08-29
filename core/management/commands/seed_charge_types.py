from django.core.management.base import BaseCommand

from core.models import ChargeType


class Command(BaseCommand):
    help = "Crée les types de charge de base (Loyer, Électricité, Eau, Internet/Wifi, Ménage)."

    def handle(self, *args, **options):
        defaults = [
            ("Loyer", True, False),
            ("Électricité", False, False),
            ("Eau", False, False),
            ("Internet / Wifi", False, True),
            ("Ménage / Entretien", False, False),
        ]
        for nom, est_loyer, est_wifi in defaults:
            obj, created = ChargeType.objects.get_or_create(
                nom=nom, defaults={"est_loyer": est_loyer, "est_wifi": est_wifi}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Créé : {nom}"))
            else:
                self.stdout.write(f"Déjà présent : {nom}")
