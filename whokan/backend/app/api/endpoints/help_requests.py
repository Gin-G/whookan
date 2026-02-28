# app/api/endpoints/help_requests.py
from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.db.session import get_user_by_id, get_help_request_by_id
from app.db.models import User
from app.db.models import HelpRequest as HelpRequestModel
from app.schemas.help_request import HelpRequest, HelpRequestCreate, HelpConfirmation
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.post("", response_model=HelpRequest)
def create_help_request(
    help_request_in: HelpRequestCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new help request
    """
    help_request = HelpRequestModel(
        id=uuid4(),
        requester_id=current_user.id,
        skill_id=help_request_in.skill_id,
        description=help_request_in.description,
        status="open"  # Set default status
    )
    
    db.add(help_request)
    db.commit()
    db.refresh(help_request)
    
    return help_request


@router.get("", response_model=List[HelpRequest])
def read_help_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve help requests
    """
    # Only return open requests from other users
    help_requests = db.query(HelpRequestModel).filter(
        HelpRequestModel.status == "open",
        HelpRequestModel.requester_id != current_user.id
    ).all()
    
    return help_requests


@router.post("/confirm", response_model=UserSchema)
def confirm_help(
    confirmation: HelpConfirmation, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm help was provided
    """
    help_request = get_help_request_by_id(db, str(confirmation.request_id))
    if not help_request:
        raise HTTPException(status_code=404, detail="Help request not found")
    
    # Verify the helper is the current user
    if confirmation.helper_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only confirm help that you provided",
        )
    
    # Update help request status
    help_request.status = "completed"
    db.commit()
    
    # Increment helper's helped count
    helper = get_user_by_id(db, str(confirmation.helper_id))
    if not helper:
        raise HTTPException(status_code=404, detail="Helper not found")
    
    helper.helped_count += 1
    db.commit()
    db.refresh(helper)
    
    # Convert the model to a dict to match the Pydantic schema
    return {
        "id": helper.id,
        "email": helper.email,
        "name": helper.name,
        "title": helper.title,
        "company": helper.company,
        "skills": [{"id": str(skill.id), "name": skill.name} for skill in helper.skills] if helper.skills else [],
        "helped_count": helper.helped_count
    }