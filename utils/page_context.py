"""Explicit dependencies shared by page modules."""

import html
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from types import SimpleNamespace

import altair as alt
import pandas as pd
import streamlit as st

from api_client import (
    change_password_api,
    create_category_api,
    create_transaction_api,
    delete_category_api,
    delete_transaction_api,
    get_categories_api,
    get_current_user,
    get_transactions_api,
    login as api_login,
    logout as api_logout,
    register as api_register,
    update_category_api,
    update_profile_api,
    update_transaction_api,
)
from components.charts import build_monthly_cashflow_chart
from components.notifications import (
    flush_notifications,
    queue_notification,
    show_notification,
)
from components.transaction_table import transaction_dataframe
from services.category_service import (
    category_label,
    category_lookup_by_id_and_type,
    category_name,
    get_category_options,
)
from services.data_service import (
    convert_category,
    convert_transaction,
    load_data,
)
from services.transaction_service import filter_transactions_by_type
from utils.api_errors import get_api_error
from utils.formatters import format_money, parse_api_date
from utils.session import get_user_id, get_user_value
from utils.ui_helpers import show_page_title
from utils.validators import normalize_transaction_type, parse_amount

