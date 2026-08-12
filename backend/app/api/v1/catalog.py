from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.catalog import CategoryGroup, City
from app.db.session import get_db
from app.schemas.catalog import CategoryGroupOut, CityOut

router = APIRouter(tags=["catalog"])


@router.get("/cities", response_model=list[CityOut])
def list_cities(db: Session = Depends(get_db)) -> list[City]:
    """34 tỉnh/thành, 6 TP trực thuộc TW xếp trước để tiện chọn trên dropdown.

    Sắp theo `id` chứ không theo `name`: id trong seed đã xếp sẵn đúng thứ tự
    mong muốn (Hà Nội, TP.HCM trước; các tỉnh theo alphabet). Sắp theo `name`
    sẽ phụ thuộc collation của Postgres — với tiếng Việt có dấu thì "Đắk Lắk"
    bị đẩy xuống sau "Vĩnh Long".
    """
    stmt = select(City).order_by(City.is_municipality.desc(), City.id)
    return list(db.scalars(stmt).all())


@router.get("/categories", response_model=list[CategoryGroupOut])
def list_category_groups(db: Session = Depends(get_db)) -> list[CategoryGroup]:
    """Cây nhóm ngành -> ngành nghề.

    selectinload để nạp categories bằng 1 query phụ thay vì N query
    (tránh N+1 khi serialize).
    """
    stmt = (
        select(CategoryGroup)
        .options(selectinload(CategoryGroup.categories))
        .order_by(CategoryGroup.display_order)
    )
    return list(db.scalars(stmt).all())
