# ----------------------------------------------------------------------
# NOTE PER LA PRODUZIONE:
#
# 1. Verifica che le dipendenze:
#    - `get_db`: Assicurati che punti al database di produzione (es. PostgreSQL o MySQL)
#      e che la gestione delle connessioni (pooling, timeout, SSL, ecc.) sia configurata correttamente.
#    - `get_current_user`: Implementa un sistema di autenticazione reale (ad es. OAuth2/JWT)
#      che validi in modo sicuro l'utente, anziché utilizzare override o dati statici.
#
# 2. Sicurezza e Gestione degli Errori:
#    - Controlla che le eccezioni vengano gestite senza esporre informazioni sensibili agli utenti.
#    - Rivedi la logica di validazione (ad es. per SMTP, Twilio, ecc.) per assicurarti che sia
#      adeguata all'ambiente di produzione.
#
# 3. Esposizione degli Endpoints:
#    - Assicurati che il router sia incluso nel router principale (definito in app/routes.py)
#      con il corretto prefisso (coerente con API_V1_STR definito in settings.py).
#
# 4. Logging e Monitoraggio:
#    - Potresti voler integrare un sistema di logging avanzato per tracciare gli errori e monitorare
#      le richieste in produzione.
#
# In sintesi, in produzione dovrai principalmente:
#    - Configurare correttamente le dipendenze (database e autenticazione).
#    - Garantire che le impostazioni di sicurezza siano adeguate e che non vengano rivelate informazioni sensibili.
#    - Verificare che il montaggio del router e l'esposizione degli endpoint siano coerenti con le configurazioni.

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import ConfigDict

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User as UserModel
from app.models.business import Business as BusinessModel
from app.schemas.business import (
    Business,
    BusinessCreate,
    BusinessUpdate,
    BusinessNotificationSettings,
    BusinessInDBBase
)
from app.core.encryption import encryption_service
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[BusinessInDBBase])
async def read_businesses(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve list of businesses for current user with decrypted sensitive data
    """
    businesses = db.query(BusinessModel)\
        .filter(BusinessModel.owner_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [
        BusinessInDBBase.model_validate(business)
        for business in businesses
    ]

@router.post("/", response_model=BusinessInDBBase, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_data: Annotated[BusinessCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Create new business with encrypted sensitive fields
    """
    # Validazione aggiuntiva prima della creazione
    if business_data.smtp_password:
        if not business_data.smtp_host or not business_data.smtp_port:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="SMTP configuration requires host and port"
            )

    db_business = BusinessModel(
        **business_data.model_dump(exclude_unset=True),
        owner_id=current_user.id
    )
    
    try:
        db.add(db_business)
        db.commit()
        db.refresh(db_business)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return BusinessInDBBase.model_validate(db_business)

@router.get("/{business_id}", response_model=BusinessInDBBase)
async def get_business(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Get business details with decrypted sensitive data
    """
    business = db.query(BusinessModel)\
        .filter(BusinessModel.id == business_id)\
        .first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    return BusinessInDBBase.model_validate(business)

@router.put("/{business_id}", response_model=BusinessInDBBase)
async def update_business(
    business_id: int,
    business_data: Annotated[BusinessUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Update business details with encrypted sensitive fields
    """
    business = db.query(BusinessModel)\
        .filter(BusinessModel.id == business_id)\
        .first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized operation"
        )

    update_data = business_data.model_dump(exclude_unset=True)
    
    # Validazione aggiornamento campi sensibili
    if 'smtp_password' in update_data:
        if not update_data.get('smtp_host') or not update_data.get('smtp_port'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="SMTP configuration requires host and port"
            )

    for field, value in update_data.items():
        setattr(business, field, value)

    try:
        db.commit()
        db.refresh(business)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return BusinessInDBBase.model_validate(business)

@router.patch("/{business_id}/notification-settings", response_model=BusinessInDBBase)
async def update_notification_settings(
    business_id: int,
    settings: Annotated[BusinessNotificationSettings, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Update notification settings with encryption
    """
    business = db.query(BusinessModel)\
        .filter(BusinessModel.id == business_id)\
        .first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized operation"
        )

    update_data = settings.model_dump(exclude_unset=True)
    
    # Validazione integrità settings
    if update_data.get('twilio_auth_token') and not update_data.get('twilio_account_sid'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Twilio configuration requires account SID"
        )

    for field, value in update_data.items():
        setattr(business, field, value)

    try:
        db.commit()
        db.refresh(business)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return BusinessInDBBase.model_validate(business)

@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """
    Delete business with all related data
    """
    business = db.query(BusinessModel)\
        .filter(BusinessModel.id == business_id)\
        .first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized operation"
        )

    try:
        db.delete(business)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return {"detail": "Business deleted successfully"}