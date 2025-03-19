from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User as UserModel
from app.models.business import Business as BusinessModel
from app.schemas.business import Business, BusinessCreate, BusinessUpdate

router = APIRouter()


@router.get("/", response_model=List[Business])
def read_businesses(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Retrieve businesses owned by current user.
    """
    businesses = (
        db.query(BusinessModel)
        .filter(BusinessModel.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return businesses


@router.post("/", response_model=Business)
def create_business(
    business_in: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create new business.
    """
    business = BusinessModel(
        **business_in.dict(),
        owner_id=current_user.id,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}", response_model=Business)
def read_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a specific business by ID.
    """
    business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Check if current user is the owner
    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this business",
        )
    
    return business


@router.put("/{business_id}", response_model=Business)
def update_business(
    business_id: int,
    business_in: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update a business.
    """
    business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Check if current user is the owner
    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this business",
        )
    
    # Update business attributes
    update_data = business_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(business, key, value)
    
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.delete("/{business_id}", response_model=Business)
def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a business.
    """
    business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Check if current user is the owner
    if business.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this business",
        )
    
    db.delete(business)
    db.commit()
    return business