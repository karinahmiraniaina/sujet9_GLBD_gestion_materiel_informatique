"""
Modèles SQLAlchemy = tables de la base de données.
8 entités, conformes au MCD :
Utilisateur, CategorieMateriel, TypeMateriel, Fournisseur,
Materiel, Affectation, SignalementPanne, HistoriqueMouvement
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="employe")  # admin / technicien / employe
    telephone = Column(String, nullable=True)
    service = Column(String, nullable=True)

    affectations = relationship("Affectation", back_populates="utilisateur")


class CategorieMateriel(Base):
    __tablename__ = "categories_materiel"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, nullable=False)
    # ex: ordinateur, peripherique, stockage, serveur_alimentation, autre

    types = relationship("TypeMateriel", back_populates="categorie")


class TypeMateriel(Base):
    __tablename__ = "types_materiel"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    # ex: ordi de bureau, ecran, ssd, onduleur...
    categorie_id = Column(Integer, ForeignKey("categories_materiel.id"), nullable=False)

    categorie = relationship("CategorieMateriel", back_populates="types")
    materiels = relationship("Materiel", back_populates="type")


class Fournisseur(Base):
    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)

    materiels = relationship("Materiel", back_populates="fournisseur")


class Materiel(Base):
    __tablename__ = "materiels"

    id = Column(Integer, primary_key=True, index=True)
    numero_serie = Column(String, unique=True, nullable=False)
    type_id = Column(Integer, ForeignKey("types_materiel.id"), nullable=False)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True)
    date_acquisition = Column(DateTime, nullable=True)
    etat = Column(String, nullable=False, default="en_service")
    # en_service / en_panne / en_maintenance / hors_service / stock
    localisation = Column(String, nullable=True)

    type = relationship("TypeMateriel", back_populates="materiels")
    fournisseur = relationship("Fournisseur", back_populates="materiels")
    affectations = relationship("Affectation", back_populates="materiel")
    signalements = relationship("SignalementPanne", back_populates="materiel")
    historiques = relationship("HistoriqueMouvement", back_populates="materiel")


class Affectation(Base):
    __tablename__ = "affectations"

    id = Column(Integer, primary_key=True, index=True)
    materiel_id = Column(Integer, ForeignKey("materiels.id"), nullable=False)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    date_affectation = Column(DateTime, default=datetime.utcnow)
    date_retour = Column(DateTime, nullable=True)
    commentaire = Column(Text, nullable=True)

    materiel = relationship("Materiel", back_populates="affectations")
    utilisateur = relationship("Utilisateur", back_populates="affectations")


class SignalementPanne(Base):
    """
    Fusionne signalement de panne + suivi de maintenance (8 entités, comme sur le MCD papier).
    Le technicien peut être un compte utilisateur du système (technicien_id)
    ou un contact externe (technicien_externe), selon ce qui est disponible.
    """
    __tablename__ = "signalements_panne"

    id = Column(Integer, primary_key=True, index=True)
    materiel_id = Column(Integer, ForeignKey("materiels.id"), nullable=False)
    declare_par_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    date_signalement = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    statut = Column(String, default="nouveau")
    # nouveau / transmis / en_maintenance / hors_service / resolu

    # Infos de prise en charge (rempli quand l'admin assigne quelqu'un)
    technicien_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    technicien_externe = Column(String, nullable=True)
    assigne_par_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    date_debut_maintenance = Column(DateTime, nullable=True)
    date_fin_maintenance = Column(DateTime, nullable=True)
    cout = Column(Float, nullable=True)
    rapport = Column(Text, nullable=True)

    materiel = relationship("Materiel", back_populates="signalements")


class HistoriqueMouvement(Base):
    __tablename__ = "historique_mouvements"

    id = Column(Integer, primary_key=True, index=True)
    materiel_id = Column(Integer, ForeignKey("materiels.id"), nullable=False)
    action = Column(String, nullable=False)
    # ex: affecte / retourne / signale_en_panne / mis_en_maintenance / resolu
    date = Column(DateTime, default=datetime.utcnow)
    utilisateur_action_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    details = Column(Text, nullable=True)

    materiel = relationship("Materiel", back_populates="historiques")