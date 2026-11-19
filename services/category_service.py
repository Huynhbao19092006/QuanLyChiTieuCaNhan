from utils.validators import normalize_transaction_type


def category_name(category_id, categories):
    """Tìm tên danh mục theo ID."""
    for category in categories:
        if category.id == category_id:
            return category.name

    return "Không xác định"

def category_label(category):
    """Nhãn hiển thị có ID để phân biệt danh mục trùng tên."""
    category_type_label = (
        "Thu nhập"
        if category.category_type == "income"
        else "Chi tiêu"
    )
    return (
        f"{category.name} · {category_type_label} "
        f"(#{category.id})"
    )

def category_lookup_by_id_and_type(categories):
    """Lập ánh xạ danh mục theo cả ID và loại."""
    return {
        (category.id, category.category_type): category
        for category in categories
    }

def get_category_options(categories, transaction_type=None):
    """Lọc danh mục theo loại giao dịch."""
    if transaction_type is None:
        return categories

    return [
        category
        for category in categories
        if normalize_transaction_type(category.category_type)
        == transaction_type
    ]
