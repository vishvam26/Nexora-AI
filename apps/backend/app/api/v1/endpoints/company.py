from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.company_settings import CompanySettings
from app.models.company_secrets import CompanySecrets
from app.models.invitation import Invitation
from app.security.dependencies import get_current_user
from app.security.crypto import encrypt_key
from app.schemas.company import (
    CompanyMemberResponse,
    CompanyMemberUpdate,
    CompanySettingsResponse,
    CompanySettingsUpdate,
    CompanySecretCreate,
    CompanySecretResponse,
    CompanyInviteRequest,
    CompanyInviteResponse,
)

router = APIRouter(
    prefix="/company",
    tags=["Company Admin & Tenancy Console"],
)


def _check_admin(user: User):
    """
    Assert that the current user is an Owner or Administrator of the company.
    """
    if not user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any company."
        )
    if user.company_role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company Owner or Administrator can perform this action."
        )


# ──────────────────────────────────────────────────────────────
# Company Member Console
# ──────────────────────────────────────────────────────────────

@router.get(
    "/members",
    response_model=List[CompanyMemberResponse],
    summary="List all company users"
)
def list_company_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company associated with this user."
        )
    
    # Query all users in company and self-join for managers
    members = db.query(User).filter(User.company_id == current_user.company_id).all()
    
    results = []
    for member in members:
        manager_name = None
        if member.manager_id:
            m = db.query(User).filter(User.id == member.manager_id).first()
            if m:
                manager_name = m.full_name
                
        results.append(CompanyMemberResponse(
            id=member.id,
            full_name=member.full_name,
            email=member.email,
            company_role=member.company_role,
            manager_id=member.manager_id,
            manager_name=manager_name,
            is_active=member.is_active,
        ))
    return results


@router.put(
    "/members/{member_id}",
    response_model=CompanyMemberResponse,
    summary="Update member role or manager hierarchy"
)
def update_company_member(
    member_id: int,
    payload: CompanyMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(current_user)
    
    member = db.query(User).filter(
        User.id == member_id,
        User.company_id == current_user.company_id
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company member not found."
        )
        
    if payload.company_role:
        if payload.company_role not in ["OWNER", "ADMIN", "EMPLOYEE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company role."
            )
        member.company_role = payload.company_role
        
    if payload.manager_id is not None:
        if payload.manager_id == member.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user cannot be their own manager."
            )
        
        # Verify manager belongs to the same company
        mgr = db.query(User).filter(
            User.id == payload.manager_id,
            User.company_id == current_user.company_id
        ).first()
        if not mgr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected manager does not exist in your company."
            )
            
        # Recursive loop detection (A -> B -> A)
        from app.services.permission_service import PermissionService
        if PermissionService.is_manager_of(db, member.id, payload.manager_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Circular management loop detected."
            )
            
        member.manager_id = payload.manager_id
    elif "manager_id" in payload.model_fields_set and payload.manager_id is None:
        member.manager_id = None
        
    db.commit()
    db.refresh(member)
    
    manager_name = None
    if member.manager_id:
        m = db.query(User).filter(User.id == member.manager_id).first()
        if m:
            manager_name = m.full_name
            
    return CompanyMemberResponse(
        id=member.id,
        full_name=member.full_name,
        email=member.email,
        company_role=member.company_role,
        manager_id=member.manager_id,
        manager_name=manager_name,
        is_active=member.is_active,
    )


# ──────────────────────────────────────────────────────────────
# Company Settings Console
# ──────────────────────────────────────────────────────────────

@router.get(
    "/settings",
    response_model=CompanySettingsResponse,
    summary="Get company preferences"
)
def get_company_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company associated with this user."
        )
        
    settings_rec = db.query(CompanySettings).filter(
        CompanySettings.company_id == current_user.company_id
    ).first()
    
    if not settings_rec:
        # Create default
        settings_rec = CompanySettings(
            company_id=current_user.company_id,
            default_llm="gemini-1.5-flash",
            theme="dark",
            max_file_size=10485760
        )
        db.add(settings_rec)
        db.commit()
        db.refresh(settings_rec)
        
    return settings_rec


@router.put(
    "/settings",
    response_model=CompanySettingsResponse,
    summary="Update company preferences"
)
def update_company_settings(
    payload: CompanySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(current_user)
    
    settings_rec = db.query(CompanySettings).filter(
        CompanySettings.company_id == current_user.company_id
    ).first()
    
    if not settings_rec:
        settings_rec = CompanySettings(company_id=current_user.company_id)
        db.add(settings_rec)
        
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(settings_rec, k, v)
        
    db.commit()
    db.refresh(settings_rec)
    return settings_rec


# ──────────────────────────────────────────────────────────────
# Company Secrets (External API Keys) Console
# ──────────────────────────────────────────────────────────────

@router.post(
    "/secrets",
    response_model=CompanySecretResponse,
    summary="Save encrypted external provider credentials"
)
def create_company_secret(
    payload: CompanySecretCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(current_user)
    
    # Encrypt raw key
    encrypted = encrypt_key(payload.api_key)
    
    # Check if provider secret already exists
    existing = db.query(CompanySecrets).filter(
        CompanySecrets.company_id == current_user.company_id,
        CompanySecrets.provider == payload.provider.upper()
    ).first()
    
    if existing:
        existing.encrypted_api_key = encrypted
        db.commit()
        db.refresh(existing)
        return existing
    else:
        sec = CompanySecrets(
            company_id=current_user.company_id,
            provider=payload.provider.upper(),
            encrypted_api_key=encrypted
        )
        db.add(sec)
        db.commit()
        db.refresh(sec)
        return sec


@router.get(
    "/secrets",
    response_model=List[CompanySecretResponse],
    summary="List active secret configurations (without revealing keys)"
)
def list_company_secrets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company associated with this user."
        )
    return db.query(CompanySecrets).filter(
        CompanySecrets.company_id == current_user.company_id
    ).all()


# ──────────────────────────────────────────────────────────────
# Company Invitations Console
# ──────────────────────────────────────────────────────────────

@router.post(
    "/invite",
    response_model=CompanyInviteResponse,
    summary="Invite user to register under company tenant"
)
def invite_user(
    payload: CompanyInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(current_user)
    
    # Verify email is not already registered
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email is already registered."
        )
        
    # Check if pending invitation exists
    existing_inv = db.query(Invitation).filter(
        Invitation.company_id == current_user.company_id,
        Invitation.email == payload.email,
        Invitation.accepted == False,
        Invitation.expires_at > datetime.utcnow()
    ).first()
    
    if existing_inv:
        return existing_inv
        
    inv = Invitation(
        company_id=current_user.company_id,
        email=payload.email,
        role=payload.role,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get(
    "/invitations",
    response_model=List[CompanyInviteResponse],
    summary="List pending invitations"
)
def list_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(current_user)
    return db.query(Invitation).filter(
        Invitation.company_id == current_user.company_id,
        Invitation.accepted == False
    ).order_by(Invitation.created_at.desc()).all()
