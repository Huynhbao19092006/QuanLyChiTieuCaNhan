from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
STYLES_DIR = BASE_DIR / "styles"


def load_css(extra_styles=None):
    """Nạp CSS dùng chung và CSS của màn hình hiện tại."""
    style_files = ["style.css"]

    if extra_styles:
        style_files.extend(extra_styles)

    for style_file in style_files:
        style_path = STYLES_DIR / style_file

        if not style_path.exists():
            st.warning(f"Không tìm thấy file styles/{style_file}")
            continue

        try:
            css = style_path.read_text(encoding="utf-8")
        except OSError as error:
            st.error(
                f"Không thể đọc file styles/{style_file}: {error}"
            )
            continue

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )

def show_page_title(title, description):
    st.title(title)
    st.caption(description)
    st.divider()
