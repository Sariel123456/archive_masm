import uuid
from django.db import models
import os
from django.core.exceptions import ValidationError  # Ajout de l'import
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.text import slugify



# ENUMS
class StatutChoices(models.TextChoices):
    ACTIF = 'actif', 'Actif'
    ATTENTE = 'attente', 'En attente'
    DESACTIVE = 'desactive', 'Désactivé'

class ImportanceChoices(models.TextChoices):
    FAIBLE = 'faible', 'Faible'
    MOYENNE = 'moyenne', 'Moyenne'
    ELEVEE = 'elevee', 'Élevée'
    CRITIQUE = 'critique', 'Critique'

class ActionTypeChoices(models.TextChoices):
    CREATION = 'creation', 'Création'
    MODIFICATION = 'modification', 'Modification'
    SUPPRESSION = 'suppression', 'Suppression'
    CONSULTATION = 'consultation', 'Consultation'

class ItemTypeChoices(models.TextChoices):
    DOSSIER = 'dossier', 'Dossier'
    PIECE = 'piece', 'Pièce'

# USER MANAGER
class UserManager(BaseUserManager):
    def create_user(self, email, matricule, password=None, **extra_fields):
        if not email:
            raise ValueError('L’email est requis')
        email = self.normalize_email(email)
        user = self.model(email=email, matricule=matricule, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, matricule, password=None, **extra_fields):
        extra_fields.setdefault('est_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('statut', 'actif')  # Pour assurer que le superuser est actif
        return self.create_user(email, matricule, password, **extra_fields)

    
    def get_by_natural_key(self, identifier):
        # Permettre la connexion avec email ou matricule
        return self.get(models.Q(email=identifier) | models.Q(matricule=identifier))

# VALIDATION HISTORY
class ValidationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    demande = models.ForeignKey('User', on_delete=models.CASCADE, related_name='demandes')
    valide_par = models.ForeignKey('User', on_delete=models.CASCADE, related_name='validations')
    statut = models.CharField(max_length=20, choices=StatutChoices.choices)
    commentaire = models.TextField(blank=True)
    date_demande = models.DateTimeField()
    date_validation = models.DateTimeField(null=True, blank=True)

# USER
class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    matricule = models.CharField(max_length=50, unique=True)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    poste = models.ForeignKey('Poste', on_delete=models.SET_NULL, null=True)
    statut = models.CharField(max_length=20, choices=StatutChoices.choices)
    est_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(auto_now_add=True)
    derniere_connexion = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['matricule']
    
    def __str__(self):
        return f"{self.prenom} {self.nom}" 
    
    
    # Ajout des propriétés et méthodes requises
    @property
    def is_active(self):
        return self.statut == StatutChoices.ACTIF
    @property
    def is_admin(self):
        return self.est_admin  # Utilise le champ est_admin au lieu de is_staff
    
    #@property
    #def is_admin(self):
        #return self.is_staff
    
    def has_perm(self, perm, obj=None):
        # Simplifié pour l'exemple. À adapter selon vos besoins
        return self.is_staff or self.est_admin
    
    def has_module_perms(self, app_label):
        # Simplifié pour l'exemple. À adapter selon vos besoins
        return self.is_staff or self.est_admin
    
    def get_full_name(self):
        return f"{self.prenom} {self.nom}"
    
    def get_short_name(self):
        return self.prenom
    
    # Propriété pour vérifier si l'utilisateur est superuser
    @property
    def is_superuser(self):
        return self.is_staff
    
    def clean(self):
        super().clean()
        if self.email and not self.email.endswith('@gouv.bj'):
            raise ValidationError({
                'email': "L'adresse email doit se terminer par @gouv.bj"
            })
    
    def save(self, *args, **kwargs):
        if self.poste:
            try:
                # Vérifier si le poste existe et n'est pas déjà occupé
                existing_user = User.objects.filter(poste=self.poste).exclude(pk=self.pk).first()
                if existing_user:
                    raise ValidationError(f"Ce poste est déjà occupé par {existing_user.prenom} {existing_user.nom}")
                
                # Si c'est une mise à jour
                if not self._state.adding:
                    # Récupérer l'ancien poste depuis la base de données
                    try:
                        old_user = User.objects.get(pk=self.pk)
                        if old_user.poste and old_user.poste != self.poste:
                            # Libérer l'ancien poste
                            old_user.poste.est_occupe = False
                            old_user.poste.save()
                    except User.DoesNotExist:
                        pass
                
                # Marquer le nouveau poste comme occupé
                poste = Poste.objects.get(pk=self.poste.pk)
                poste.est_occupe = True
                poste.save()
            
            except Poste.DoesNotExist:
                pass

        super().save(*args, **kwargs)
# DIRECTION, SERVICE, POSTE
class Direction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom  # Afficher le nom de la direction

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nom  # Afficher le nom de la direction

class Poste(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    est_occupe = models.BooleanField(default=False)
    est_chef = models.BooleanField(default=False)
    
    def __str__(self):
        return self.nom  # Afficher le nom de la direction

# FOLDER TYPE ET PIECE TYPE
class FolderType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cree_a = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom  # Afficher le nom de la direction

class PieceType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type_dossier = models.ForeignKey(FolderType, on_delete=models.SET_NULL, null=True, blank=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cree_a = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom  # Afficher le nom de la direction

# KEYWORD
class Keyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nom

# FOLDER
class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True)
    dossier_parent = models.ForeignKey(FolderType, on_delete=models.PROTECT)
    provenance = models.CharField(max_length=255)
    importance = models.CharField(max_length=20, choices=ImportanceChoices.choices)
    dossier_date = models.DateField()
    creation_date = models.DateTimeField(auto_now_add=True)
    derniere_modification = models.DateTimeField(auto_now=True)
    est_public = models.BooleanField(default=False)
    keyword = models.ManyToManyField(Keyword, through='FolderKeyword')
    est_supprime = models.BooleanField(default=False)
    
    def __str__(self):
        return self.titre
    
    

def piece_upload_to(instance, filename):
    base, ext = os.path.splitext(filename)
    titre = slugify(instance.titre)
    return f"pieces/{titre}_{uuid.uuid4().hex}{ext}"

# PIECE
class Piece(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titre = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to=piece_upload_to)
    fichier_taille = models.BigIntegerField()
    piece_date = models.DateField()
    date_televersement = models.DateTimeField(auto_now_add=True)
    createur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    entite = models.CharField(max_length=100)
    numero = models.CharField(max_length=50)
    type = models.ForeignKey(PieceType, on_delete=models.CASCADE)
    duree_vie = models.IntegerField()
    est_public = models.BooleanField(default=False)
    keyword = models.ManyToManyField(Keyword, through='PieceKeyword')
    est_supprime = models.BooleanField(default=False)
    importance = models.CharField(max_length=20, choices=ImportanceChoices.choices)
    dossier = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        related_name='pieces',
        null=True,
        blank=True
    )
    
    def __str__(self):
        return self.titre
    



# HISTORIQUE
class PieceHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50, choices=ActionTypeChoices.choices)
    action_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

class FolderHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dossier = models.ForeignKey(Folder, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50, choices=ActionTypeChoices.choices)
    action_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

# PERMISSIONS
class FolderPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dossier = models.ForeignKey(Folder, on_delete=models.CASCADE)
    beneficiaire = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name='permissions_dossier', null=True, blank=True)
    direction_beneficiaire = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True)
    structure_beneficiaire = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    peut_lire = models.BooleanField(default=False)
    peut_editer = models.BooleanField(default=False)
    peut_supprime = models.BooleanField(default=False)
    donneur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dossier_donnes')
    attribution_date = models.DateTimeField(auto_now_add=True)

class PiecePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    beneficiaire = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name='permissions_piece', null=True, blank=True)
    direction_beneficiaire = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True)
    structure_beneficiaire = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    peut_lire = models.BooleanField(default=False)
    peut_editer = models.BooleanField(default=False)
    peut_supprime = models.BooleanField(default=False)
    donneur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='piece_donnes')
    attribution_date = models.DateTimeField(auto_now_add=True)

# CORBEILLE
class TrashItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_type = models.CharField(max_length=50, choices=ItemTypeChoices.choices)
    piece = models.ForeignKey(Piece, on_delete=models.SET_NULL, null=True, blank=True)
    dossier = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True)
    supprime_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='items_supprimes')
    date_suppression = models.DateTimeField(auto_now_add=True)
    justification = models.TextField(blank=True)
    est_restauré = models.BooleanField(default=False)
    date_restoration = models.DateTimeField(null=True, blank=True)
    restauré_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='items_restaures')

# KEYWORDS RELATIONS
class FolderKeyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)

class PieceKeyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
