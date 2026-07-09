"""
Schémas Pydantic = validation des données entrantes/sortantes de l'API.
Différent des models.py (qui définissent les tables DB).
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ---------- Utilisateur ----------
class UtilisateurBase(BaseModel):
    nom: str
    email: EmailStr
    role: str = "employe"
    telephone: Optional[str] = None
    service: Optional[str] = None


class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str


class UtilisateurOut(UtilisateurBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Auth / Token ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ---------- Catégorie de matériel ----------
class CategorieMaterielBase(BaseModel):
    nom: str


class CategorieMaterielCreate(CategorieMaterielBase):
    pass


class CategorieMaterielOut(CategorieMaterielBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Type de matériel ----------
class TypeMaterielBase(BaseModel):
    nom: str
    categorie_id: int


class TypeMaterielCreate(TypeMaterielBase):
    pass


class TypeMaterielOut(TypeMaterielBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Fournisseur ----------
class FournisseurBase(BaseModel):
    nom: str
    contact: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None


class FournisseurCreate(FournisseurBase):
    pass


class FournisseurOut(FournisseurBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Matériel ----------
class MaterielBase(BaseModel):
    numero_serie: str
    type_id: int
    fournisseur_id: Optional[int] = None
    date_acquisition: Optional[datetime] = None
    etat: str = "en_service"
    localisation: Optional[str] = None


class MaterielCreate(MaterielBase):
    pass


class MaterielOut(MaterielBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Affectation ----------
class AffectationBase(BaseModel):
    materiel_id: int
    utilisateur_id: int
    commentaire: Optional[str] = None


class AffectationCreate(AffectationBase):
    pass


class AffectationOut(AffectationBase):
    id: int
    date_affectation: datetime
    date_retour: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Signalement de panne (+ suivi maintenance fusionné) ----------
class SignalementPanneBase(BaseModel):
    materiel_id: int
    description: str


class SignalementPanneCreate(SignalementPanneBase):
    pass


class SignalementPanneOut(SignalementPanneBase):
    id: int
    declare_par_id: int
    date_signalement: datetime
    statut: str
    technicien_id: Optional[int] = None
    technicien_externe: Optional[str] = None
    assigne_par_id: Optional[int] = None
    date_debut_maintenance: Optional[datetime] = None
    date_fin_maintenance: Optional[datetime] = None
    cout: Optional[float] = None
    rapport: Optional[str] = None

    class Config:
        from_attributes = True


class AssignerMaintenance(BaseModel):
    """Utilisé par l'admin pour assigner un technicien à un signalement existant."""
    technicien_id: Optional[int] = None
    technicien_externe: Optional[str] = None


class CloturerMaintenance(BaseModel):
    """Utilisé pour clôturer une maintenance (résolu)."""
    rapport: str
    cout: Optional[float] = None