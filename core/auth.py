from django.contrib.auth.backends import ModelBackend
from django.db import models  # Ajout de l'import models
from .models import User

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        try:
            print(f"Tentative d'authentification avec identifier={identifier}")
            # Utiliser models.Q correctement
            user = User.objects.get(
                models.Q(email=identifier) | models.Q(matricule=identifier)
            )
            print(f"Utilisateur trouvé: {user}")
            if user.check_password(password):
                print("Mot de passe correct")
                return user
            print("Mot de passe incorrect")
            return None
        except User.DoesNotExist:
            print("Utilisateur non trouvé")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None