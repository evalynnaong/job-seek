from __future__ import annotations

import html

import streamlit as st

from services.image.logo_preprocess import preprocess_logo


def display_logo(icon_url: str | None, title: str, *, width: int = 64) -> None:
    icon = (icon_url or "").strip()
    if icon:
        st.image(preprocess_logo(icon), width=width)
        return

    initial = html.escape((title.strip()[:1] or "?").upper())
    st.markdown(
        f"""
        <div style="
            width: {width}px;
            height: {width}px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
            font-size: {max(18, width // 2)}px;
            font-weight: 700;
            line-height: 1;
        ">{initial}</div>
        """,
        unsafe_allow_html=True,
    )
