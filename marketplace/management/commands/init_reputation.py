from django.core.management.base import BaseCommand
from marketplace.models import Prestataire, ReputationScore


class Command(BaseCommand):
    help = 'Initialise les scores de réputation pour tous les prestataires existants'

    def handle(self, *args, **options):
        prestataires = Prestataire.objects.all()
        total = prestataires.count()
        self.stdout.write(f'Initialisation de {total} prestataires...')

        updated = 0
        for p in prestataires:
            try:
                rep = ReputationScore.update_score(p)
                self.stdout.write(
                    f'  ✓ {p} → score {rep.score_global}/5 '
                    f'({rep.nb_avis} avis, badge={rep.badge_confiance})'
                )
                updated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {p} → {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ {updated}/{total} scores initialisés.'
        ))
