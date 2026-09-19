"""Wizard stepper and navigation helpers."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_wizard_stepper(current_step: int, steps: list = None) -> None:
    """Render a horizontal progress stepper showing the wizard flow.

    Args:
        current_step: Current step number (1-indexed).
        steps: List of step dicts with keys: key, label, icon.
               Defaults to WIZARD_STEPS.
    """
    from streamlit_app.utils.constants import WIZARD_STEPS, BORDER_COLOR

    steps = steps or WIZARD_STEPS
    total_steps = len(steps)

    step_columns = st.columns(total_steps, gap="small")

    for idx, (col, step) in enumerate(zip(step_columns, steps), start=1):
        step_num = idx
        is_active = step_num == current_step
        is_completed = step_num < current_step
        is_pending = step_num > current_step

        if is_completed:
            circle_bg = "#10B981"
            circle_text = "#FFFFFF"
            circle_content = "✓"
            label_color = "#94A3B8"
            label_weight = "500"
        elif is_active:
            circle_bg = "linear-gradient(135deg, #4F46E5, #6366F1)"
            circle_text = "#FFFFFF"
            circle_content = str(step_num)
            label_color = "#F1F5F9"
            label_weight = "700"
        else:  # pending
            circle_bg = "#1E293B"
            circle_text = "#64748B"
            circle_content = str(step_num)
            label_color = "#64748B"
            label_weight = "500"

        with col:
            render_html(
                f"""
                <div style="text-align: center; padding: 0.5rem 0.25rem;">
                    <div style="
                        width: 36px;
                        height: 36px;
                        margin: 0 auto 0.5rem;
                        border-radius: 50%;
                        background: {circle_bg};
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: 700;
                        color: {circle_text};
                        font-size: 0.95rem;
                        border: 2px solid {'#10B981' if is_completed else ('#4F46E5' if is_active else '#334155')};
                    ">{circle_content}</div>
                    <div style="
                        font-size: 0.75rem;
                        color: {label_color};
                        font-weight: {label_weight};
                        line-height: 1.2;
                    ">
                        <span style="margin-right: 0.2rem;">{step['icon']}</span>
                        {step['label']}
                    </div>
                </div>
                """,
            )


def render_wizard_nav(
    current_step: int,
    total_steps: int = 5,
    next_label: str = "Next",
    back_label: str = "← Back",
    next_disabled: bool = False,
    show_back: bool = True,
    show_next: bool = True,
    next_key: str = "wizard_next",
    back_key: str = "wizard_back",
    submit: bool = False,
) -> tuple[bool, bool]:
    """Render Back / Next buttons for the wizard flow.

    Args:
        submit: If True, use ``st.form_submit_button`` instead of
            ``st.button``. Required when this function is called from
            inside an ``st.form`` block, since Streamlit does not allow
            regular buttons inside forms.

    Returns:
        Tuple of (back_clicked, next_clicked) booleans.
    """
    back_clicked = False
    next_clicked = False

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_left:
        if show_back and current_step > 1:
            if submit:
                back_clicked = st.form_submit_button(
                    back_label, key=back_key, type="secondary", use_container_width=True
                )
            else:
                if st.button(back_label, key=back_key, type="secondary", use_container_width=True):
                    back_clicked = True

    with col_right:
        if show_next:
            label = next_label
            if current_step == total_steps - 1:
                label = "Start Inspection →"
            elif current_step == total_steps:
                label = "Done"
            if submit:
                next_clicked = st.form_submit_button(
                    label, key=next_key, type="primary",
                    use_container_width=True, disabled=next_disabled,
                )
            else:
                if st.button(label, key=next_key, type="primary",
                             use_container_width=True, disabled=next_disabled):
                    next_clicked = True

    return back_clicked, next_clicked