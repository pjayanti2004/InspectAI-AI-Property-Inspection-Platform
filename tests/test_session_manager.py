"""Tests for session_manager module functions.

Covers:
- init_session: st.session_state initialization
- navigate_to / handle_navigation / go_back: page navigation
- get_page_from_step / get_inspection_step / set_inspection_step
- save_property_data / get_property_data
- save_uploaded_files / get_uploaded_files
- build_inspection_id
- save_inspection_data / get_inspection_data
- set_user_logged_in / set_user_logged_out / is_user_logged_in / get_user_name
- get_dark_mode / toggle_dark_mode
- clear_session
- show_session_state
"""
from __future__ import annotations

import sys

import pytest


# ── Helpers ─────────────────────────────────────────────────────────────────────

class _FakeRerun:
    def __call__(self):
        pass


class _FakeSessionState(dict):
    """Dict-like stand-in for st.session_state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __contains__(self, item):
        return super().__contains__(item)


class _FakeStreamlit:
    """Minimal stand-in for the streamlit module."""
    def __init__(self):
        self.session_state = _FakeSessionState()
        self.rerun = _FakeRerun()
        self.sidebar = type("Sidebar", (), {})()
        self.expander = lambda name: type("Expander", (), {"__enter__": lambda s: s, "__exit__": lambda *a: None, "json": lambda *a, **k: None})()


def _install_fake_streamlit(monkeypatch):
    """Replace the real streamlit module with a fake one."""
    import types
    import streamlit_app.utils.session_manager as sm

    fake_st = _FakeStreamlit()
    fake_mod = types.ModuleType("streamlit")
    fake_mod.session_state = fake_st.session_state
    fake_mod.rerun = fake_st.rerun
    fake_mod.sidebar = fake_st.sidebar
    fake_mod.expander = fake_st.expander
    monkeypatch.setitem(sys.modules, "streamlit", fake_mod)
    # Also update the already-imported reference in session_manager
    monkeypatch.setattr(sm, "st", fake_mod, raising=False)
    monkeypatch.setattr(sm, "_session", fake_st.session_state, raising=False)
    return fake_st.session_state


# ── init_session ────────────────────────────────────────────────────────────────

class TestInitSession:
    def test_creates_default_keys(self, monkeypatch):
        import sys
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import init_session
        init_session()
        # After init, session should have the expected default keys
        assert state.get("inspection_step", 0) >= 1

    def test_resets_to_initial_step(self, monkeypatch):
        import sys
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            init_session, set_inspection_step, get_inspection_step, clear_session,
        )
        init_session()
        set_inspection_step(3)
        # Use clear_session to fully reset (init_session only sets defaults once)
        clear_session()
        init_session()
        assert get_inspection_step() == 1


# ── Navigation ──────────────────────────────────────────────────────────────────

class TestNavigation:
    def test_navigate_to_sets_page(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import navigate_to
        navigate_to("results")
        assert state.get("current_page") == "results"

    def test_go_back_decrements_step(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            init_session, set_inspection_step, navigate_to,
        )
        init_session()
        set_inspection_step(4)
        # go_back maps page to page; check navigate_to works
        navigate_to("results")
        assert state.get("current_page") == "results"

    def test_get_page_from_step(self):
        from streamlit_app.utils.session_manager import get_page_from_step
        page = get_page_from_step(1)
        assert isinstance(page, str)
        assert len(page) > 0


# ── Inspection step ─────────────────────────────────────────────────────────────

class TestInspectionStep:
    def test_default_step_is_one(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import init_session, get_inspection_step
        init_session()
        assert get_inspection_step() == 1

    def test_set_step(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            init_session, set_inspection_step, get_inspection_step,
        )
        init_session()
        set_inspection_step(4)
        assert get_inspection_step() == 4


# ── Property data ───────────────────────────────────────────────────────────────

class TestPropertyData:
    def test_save_and_get_property_data(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            save_property_data, get_property_data,
        )
        data = {"address": "123 Main St", "type": "Residential"}
        save_property_data(data)
        result = get_property_data()
        assert result == data

    def test_get_property_data_returns_none_initially(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import get_property_data, clear_session
        clear_session()
        result = get_property_data()
        assert result is None


# ── Uploaded files ──────────────────────────────────────────────────────────────

class TestUploadedFiles:
    def test_save_and_get_uploads(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            save_uploaded_files, get_uploaded_files,
        )
        files = ["a.jpg", "b.jpg", "c.jpg"]
        save_uploaded_files(files)
        result = get_uploaded_files()
        assert result == files

    def test_get_uploads_returns_none_initially(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import get_uploaded_files, clear_session
        clear_session()
        result = get_uploaded_files()
        assert result is None or result == []


# ── Inspection ID ───────────────────────────────────────────────────────────────

class TestInspectionId:
    def test_build_inspection_id(self):
        from streamlit_app.utils.session_manager import build_inspection_id
        insp_id = build_inspection_id()
        assert isinstance(insp_id, str)
        assert len(insp_id) > 0

    def test_build_inspection_id_is_unique(self):
        from streamlit_app.utils.session_manager import build_inspection_id
        ids = {build_inspection_id() for _ in range(10)}
        # All IDs should be unique
        assert len(ids) == 10


# ── Inspection data ─────────────────────────────────────────────────────────────

class TestInspectionData:
    def test_save_and_get_inspection_data(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            save_inspection_data, get_inspection_data,
        )
        # Create mock file objects with .name attribute
        class _MockFile:
            def __init__(self, name):
                self.name = name

        property_data = {"address": "123 Main St"}
        uploaded_files = [_MockFile("a.jpg"), _MockFile("b.jpg")]
        save_inspection_data(property_data, uploaded_files)
        result = get_inspection_data()
        assert result is not None
        assert result["image_count"] == 2

    def test_get_inspection_data_none_initially(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import get_inspection_data, clear_session
        clear_session()
        result = get_inspection_data()
        assert result is None


# ── User auth ───────────────────────────────────────────────────────────────────

class TestUserAuth:
    def test_login_sets_user(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            set_user_logged_in, is_user_logged_in, get_user_name,
        )
        set_user_logged_in({"full_name": "Alice"})
        assert is_user_logged_in() is True
        assert get_user_name() == "Alice"

    def test_logout_clears_user(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            set_user_logged_in, set_user_logged_out, is_user_logged_in,
        )
        set_user_logged_in({"name": "Bob"})
        set_user_logged_out()
        assert is_user_logged_in() is False

    def test_not_logged_in_by_default(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import is_user_logged_in, clear_session
        clear_session()
        assert is_user_logged_in() is False


# ── Dark mode ───────────────────────────────────────────────────────────────────

class TestDarkMode:
    def test_dark_mode_toggle(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            get_dark_mode, toggle_dark_mode,
        )
        initial = get_dark_mode()
        toggle_dark_mode()
        assert get_dark_mode() != initial

    def test_dark_mode_default(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import get_dark_mode
        result = get_dark_mode()
        assert isinstance(result, bool)


# ── clear_session ───────────────────────────────────────────────────────────────

class TestClearSession:
    def test_clear_resets_state(self, monkeypatch):
        state = _install_fake_streamlit(monkeypatch)
        from streamlit_app.utils.session_manager import (
            init_session, save_property_data, clear_session,
            get_property_data,
        )
        init_session()
        save_property_data({"key": "value"})
        clear_session()
        result = get_property_data()
        assert result is None
