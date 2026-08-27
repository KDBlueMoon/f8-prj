from fastapi import APIRouter

from models.category import CategoryGroup
from schemas.category import CategoryGroupOut

router = APIRouter(tags=["Public"])


@router.get("/categories", response_model=list[CategoryGroupOut])
def list_categories() -> list[CategoryGroup]:
    return CategoryGroup.get_list(order_by=CategoryGroup.display_order)
