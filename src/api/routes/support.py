from fastapi import APIRouter, Depends
from src.database.models import User
from src.dependencies import get_current_user, get_llm_client, get_order_repository
from src.services.support_service import SupportQuestion, SupportAnswer, answer_support


router = APIRouter(prefix="/support", tags=["support"])

@router.post("/", response_model=SupportAnswer)
async def support(
    body: SupportQuestion,
    current_user: User = Depends(get_current_user),
    order_repo=Depends(get_order_repository),
    client=Depends(get_llm_client),
):
    return await answer_support(
        question=body.question,
        current_user_id=current_user.id,
        order_repo=order_repo,
        client=client,
    )