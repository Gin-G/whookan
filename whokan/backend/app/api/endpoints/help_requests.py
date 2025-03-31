from typing import Any, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.db.session import help_requests_db, users_db, get_user_by_id, get_help_request_by_id
from app.models.user import User
from app.models.help_request import HelpRequest as HelpRequestModel
from app.schemas.help_request import HelpRequest, HelpRequestCreate, HelpConfirmation
from app.schemas.user import User as UserSchema  # Import Pydantic User schema

router = APIRouter()


@router.post("", response_model=HelpRequest)
def create_help_request(
    help_request_in: HelpRequestCreate, current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new help request
    """
    request_id = uuid4()
    help_request = HelpRequestModel(
        id=request_id,
        requester_id=current_user.id,
        skill_id=help_request_in.skill_id,
        description=help_request_in.description,
    )
    help_requests_db[str(request_id)] = help_request
    return help_request


@router.get("", response_model=List[HelpRequest])
def read_help_requests(current_user: User = Depends(get_current_user)) -> Any:
    """
    Retrieve help requests
    """
    # Only return open requests from other users
    return [
        request for request in help_requests_db.values()
        if request.status == "open" and request.requester_id != current_user.id
    ]


@router.post("/confirm", response_model=UserSchema)  # Use Pydantic schema here
def confirm_help(
    confirmation: HelpConfirmation, current_user: User = Depends(get_current_user)
) -> Any:
    """
    Confirm help was provided
    """
    help_request = get_help_request_by_id(str(confirmation.request_id))
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
    help_requests_db[str(confirmation.request_id)] = help_request
    
    # Increment helper's helped count
    helper = get_user_by_id(str(confirmation.helper_id))
    if not helper:
        raise HTTPException(status_code=404, detail="Helper not found")
    
    helper.helped_count += 1
    users_db[helper.email] = helper
    
    # Convert the model to a dict first to match the Pydantic schema's structure
    # This is a simplified approach for the in-memory database
    return {
        "id": helper.id,
        "email": helper.email,
        "name": helper.name,
        "title": helper.title,
        "company": helper.company,
        "skills": helper.skills,
        "helped_count": helper.helped_count
    }