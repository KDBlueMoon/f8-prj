from fastapi import APIRouter, Path, Request

from app.core.errors import AppError
from app.core.rate_limit import limiter
from app.integrations import vietqr
from app.schemas.company import TaxCodeLookupOut
from app.schemas.validators import validate_tax_code

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/lookup-tax-code/{tax_code}", response_model=TaxCodeLookupOut)
@limiter.limit("10/minute")
def lookup_tax_code(
    request: Request,
    tax_code: str = Path(min_length=10, max_length=14),
) -> TaxCodeLookupOut:
    """Tra cứu doanh nghiệp theo mã số thuế để tự điền form đăng ký.

    Công khai vì người dùng cần dùng trước khi có tài khoản. Có giới hạn tần
    suất để không biến endpoint này thành công cụ quét dữ liệu doanh nghiệp
    hàng loạt qua hệ thống của mình.

    Chỉ trả 4 trường VietQR có. Người đại diện, số điện thoại, email, ngày cấp,
    quy mô và lĩnh vực phải nhập tay.
    """
    try:
        cleaned_tax_code = validate_tax_code(tax_code)
    except ValueError as error:
        # Mã số thuế nằm trên đường dẫn nên Pydantic không kiểm hộ được như với
        # body — phải tự chuyển lỗi sang format lỗi chung của hệ thống.
        raise AppError("INVALID_TAX_CODE", str(error)) from error

    info = vietqr.lookup_tax_code(cleaned_tax_code)
    return TaxCodeLookupOut(
        tax_code=info.tax_code,
        company_name=info.company_name,
        international_name=info.international_name,
        short_name=info.short_name,
        headquarters_address=info.headquarters_address,
    )
