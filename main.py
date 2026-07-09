#Point d'entrée de l'application FastAPI.
#Toutes les routes sont ici (version simplifiée, 8 entités).

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models
import schemas
import security

# Crée les tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestion des Matériels Informatiques")

# CORS : nécessaire pour que le frontend (fichier .html ouvert dans le navigateur,
# ou servi sur un autre port) puisse appeler cette API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== AUTH ====================

@app.post("/auth/register", response_model=schemas.UtilisateurOut)
def register(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    existe = db.query(models.Utilisateur).filter(models.Utilisateur.email == utilisateur.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    nouvel_utilisateur = models.Utilisateur(
        nom=utilisateur.nom,
        email=utilisateur.email,
        mot_de_passe_hash=security.hash_mot_de_passe(utilisateur.mot_de_passe),
        role=utilisateur.role,
        telephone=utilisateur.telephone,
        service=utilisateur.service,
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    return nouvel_utilisateur


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.email == form_data.username).first()
    if not utilisateur or not security.verifier_mot_de_passe(form_data.password, utilisateur.mot_de_passe_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    token = security.creer_access_token(data={"sub": utilisateur.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UtilisateurOut)
def me(utilisateur=Depends(security.get_current_user)):
    return utilisateur


@app.get("/utilisateurs", response_model=list[schemas.UtilisateurOut])
def lister_utilisateurs(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.Utilisateur).all()


# ==================== CATÉGORIES DE MATÉRIEL ====================

@app.post("/categories", response_model=schemas.CategorieMaterielOut)
def creer_categorie(
    categorie: schemas.CategorieMaterielCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    nouvelle = models.CategorieMateriel(**categorie.model_dump())
    db.add(nouvelle)
    db.commit()
    db.refresh(nouvelle)
    return nouvelle


@app.get("/categories", response_model=list[schemas.CategorieMaterielOut])
def lister_categories(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.CategorieMateriel).all()


# ==================== TYPES DE MATÉRIEL ====================

@app.post("/types", response_model=schemas.TypeMaterielOut)
def creer_type(
    type_materiel: schemas.TypeMaterielCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    nouveau = models.TypeMateriel(**type_materiel.model_dump())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@app.get("/types", response_model=list[schemas.TypeMaterielOut])
def lister_types(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.TypeMateriel).all()


# ==================== FOURNISSEURS ====================

@app.post("/fournisseurs", response_model=schemas.FournisseurOut)
def creer_fournisseur(
    fournisseur: schemas.FournisseurCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    nouveau = models.Fournisseur(**fournisseur.model_dump())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@app.get("/fournisseurs", response_model=list[schemas.FournisseurOut])
def lister_fournisseurs(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.Fournisseur).all()


# ==================== MATÉRIEL ====================

@app.post("/materiels", response_model=schemas.MaterielOut)
def creer_materiel(
    materiel: schemas.MaterielCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    nouveau = models.Materiel(**materiel.model_dump())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@app.get("/materiels", response_model=list[schemas.MaterielOut])
def lister_materiels(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.Materiel).all()


@app.get("/materiels/{materiel_id}", response_model=schemas.MaterielOut)
def obtenir_materiel(materiel_id: int, db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    materiel = db.query(models.Materiel).filter(models.Materiel.id == materiel_id).first()
    if not materiel:
        raise HTTPException(status_code=404, detail="Matériel introuvable")
    return materiel


# ==================== AFFECTATIONS ====================

@app.post("/affectations", response_model=schemas.AffectationOut)
def creer_affectation(
    affectation: schemas.AffectationCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    nouvelle = models.Affectation(**affectation.model_dump())
    db.add(nouvelle)
    db.commit()
    db.refresh(nouvelle)

    historique = models.HistoriqueMouvement(
        materiel_id=affectation.materiel_id,
        action="affecte",
        utilisateur_action_id=utilisateur.id,
        details=f"Affecté à l'utilisateur {affectation.utilisateur_id}",
    )
    db.add(historique)
    db.commit()

    return nouvelle


@app.get("/affectations", response_model=list[schemas.AffectationOut])
def lister_affectations(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.Affectation).all()


@app.patch("/affectations/{affectation_id}/retour", response_model=schemas.AffectationOut)
def retourner_materiel(
    affectation_id: int,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    affectation = db.query(models.Affectation).filter(models.Affectation.id == affectation_id).first()
    if not affectation:
        raise HTTPException(status_code=404, detail="Affectation introuvable")

    affectation.date_retour = datetime.utcnow()
    db.commit()
    db.refresh(affectation)

    historique = models.HistoriqueMouvement(
        materiel_id=affectation.materiel_id,
        action="retourne",
        utilisateur_action_id=utilisateur.id,
    )
    db.add(historique)
    db.commit()

    return affectation


# ==================== SIGNALEMENTS DE PANNE + MAINTENANCE (fusionnés) ====================

@app.post("/pannes", response_model=schemas.SignalementPanneOut)
def signaler_panne(
    signalement: schemas.SignalementPanneCreate,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.get_current_user),  # tout utilisateur connecté peut signaler
):
    nouveau = models.SignalementPanne(
        materiel_id=signalement.materiel_id,
        description=signalement.description,
        declare_par_id=utilisateur.id,
    )
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)

    materiel = db.query(models.Materiel).filter(models.Materiel.id == signalement.materiel_id).first()
    if materiel:
        materiel.etat = "en_panne"
        db.commit()

    historique = models.HistoriqueMouvement(
        materiel_id=signalement.materiel_id,
        action="signale_en_panne",
        utilisateur_action_id=utilisateur.id,
        details=signalement.description,
    )
    db.add(historique)
    db.commit()

    return nouveau


@app.get("/pannes", response_model=list[schemas.SignalementPanneOut])
def lister_pannes(db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.SignalementPanne).all()


@app.patch("/pannes/{signalement_id}/assigner", response_model=schemas.SignalementPanneOut)
def assigner_technicien(
    signalement_id: int,
    assignation: schemas.AssignerMaintenance,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin")),
):
    """L'admin assigne un technicien (interne ou externe) à un signalement de panne."""
    signalement = db.query(models.SignalementPanne).filter(models.SignalementPanne.id == signalement_id).first()
    if not signalement:
        raise HTTPException(status_code=404, detail="Signalement introuvable")

    signalement.technicien_id = assignation.technicien_id
    signalement.technicien_externe = assignation.technicien_externe
    signalement.assigne_par_id = utilisateur.id
    signalement.date_debut_maintenance = datetime.utcnow()
    signalement.statut = "en_maintenance"
    db.commit()
    db.refresh(signalement)

    materiel = db.query(models.Materiel).filter(models.Materiel.id == signalement.materiel_id).first()
    if materiel:
        materiel.etat = "en_maintenance"
        db.commit()

    historique = models.HistoriqueMouvement(
        materiel_id=signalement.materiel_id,
        action="mis_en_maintenance",
        utilisateur_action_id=utilisateur.id,
        details=assignation.technicien_externe or f"technicien id={assignation.technicien_id}",
    )
    db.add(historique)
    db.commit()

    return signalement


@app.patch("/pannes/{signalement_id}/cloturer", response_model=schemas.SignalementPanneOut)
def cloturer_signalement(
    signalement_id: int,
    cloture: schemas.CloturerMaintenance,
    db: Session = Depends(get_db),
    utilisateur=Depends(security.require_role("admin", "technicien")),
):
    """Clôture le signalement une fois la réparation terminée."""
    signalement = db.query(models.SignalementPanne).filter(models.SignalementPanne.id == signalement_id).first()
    if not signalement:
        raise HTTPException(status_code=404, detail="Signalement introuvable")

    signalement.date_fin_maintenance = datetime.utcnow()
    signalement.rapport = cloture.rapport
    signalement.cout = cloture.cout
    signalement.statut = "resolu"
    db.commit()
    db.refresh(signalement)

    materiel = db.query(models.Materiel).filter(models.Materiel.id == signalement.materiel_id).first()
    if materiel:
        materiel.etat = "en_service"
        db.commit()

    historique = models.HistoriqueMouvement(
        materiel_id=signalement.materiel_id,
        action="resolu",
        utilisateur_action_id=utilisateur.id,
        details=cloture.rapport,
    )
    db.add(historique)
    db.commit()

    return signalement


# ==================== HISTORIQUE ====================

@app.get("/historique/{materiel_id}")
def obtenir_historique(materiel_id: int, db: Session = Depends(get_db), utilisateur=Depends(security.get_current_user)):
    return db.query(models.HistoriqueMouvement).filter(
        models.HistoriqueMouvement.materiel_id == materiel_id
    ).order_by(models.HistoriqueMouvement.date).all()


# ==================== RACINE ====================

@app.get("/")
def racine():
    return {"message": "API Gestion des Matériels Informatiques"}