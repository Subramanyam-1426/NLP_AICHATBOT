from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_FILE = str(Path(__file__).resolve().parents[1] / "app.py")


def _app_on(page: str) -> AppTest:
    app = AppTest.from_file(APP_FILE, default_timeout=60).run()
    if app.session_state.get("user") is None:
        app.button(key="continue_as_guest").click().run()
    if app.radio[0].value != page:
        app.radio[0].set_value(page).run()
    assert not app.exception
    return app


def test_home_open_actions_route_to_each_page():
    app = _app_on("Home")
    targets = ["Chat", "NLTK Lab", "Document Q&A", "Analytics", "Model Training", "Demo Mode"]
    assert not any(button.key == "home_open_home" for button in app.button)
    app.button(key="home_start_chatting").click().run()
    assert app.radio[0].value == "Chat"
    app.radio[0].set_value("Home").run()
    for target in targets:
        key = f"home_open_{target.lower().replace(' ', '_')}"
        app.button(key=key).click().run()
        assert not app.exception
        assert app.radio[0].value == target
        if target != "Home":
            app.radio[0].set_value("Home").run()


def test_appearance_toggle_persists_in_session():
    app = _app_on("Home")
    app.toggle[0].set_value(True).run()
    assert app.session_state["dark_mode"] is True
    assert not app.exception


def test_chat_history_has_a_dedicated_navigation_page():
    app = _app_on("Chat history")
    assert app.radio[0].value == "Chat history"
    assert any("Guest chats are not saved" in str(item.value) for item in app.info)

    app.session_state["user"] = {
        "id": -999,
        "username": "history_test",
        "display_name": "History Test",
        "role": "user",
    }
    app.session_state["guest_mode"] = False
    app.run()
    assert any("No saved conversations yet" in str(item.value) for item in app.info)
    assert any(button.key == "history_page_new_chat" for button in app.button)
    app.button(key="history_page_new_chat").click().run()
    assert app.radio[0].value == "Chat"
    app.button(key="open_chat_history").click().run()
    assert app.radio[0].value == "Chat history"
    assert not app.exception


def test_chat_suggestion_feedback_nltk_shortcut_and_clear():
    app = _app_on("Chat")
    app.button(key="chat_suggestion_What is NLP?").click().run()
    assert any("Natural Language Processing" in str(item.value) for item in app.markdown)
    app.button(key="up_0").click().run()
    assert list(app.session_state["chat_feedback_votes"].values()) == [1]
    app.button(key="nltk_0").click().run()
    assert app.radio[0].value == "NLTK Lab"

    app = _app_on("Chat")
    app.button(key="chat_suggestion_What is NLP?").click().run()
    next(button for button in app.button if button.label == "Clear chat").click().run()
    app.button(key="confirm_guest_clear").click().run()
    assert app.session_state["chat_history"] == []
    assert not app.exception


def test_nltk_lab_input_and_tabs_render():
    app = _app_on("NLTK Lab")
    assert len(app.tabs) == 7
    app.text_area[0].set_value("Tokenize this short sample.").run()
    assert len(app.dataframe) >= 1
    assert not app.exception


def test_document_query_and_clear_index():
    app = _app_on("Document Q&A")
    assert app.session_state["document_auto_sample_disabled"] is False
    app.text_input(key="document_question").set_value("What courses are offered?").run()
    assert not app.exception
    next(button for button in app.button if button.label == "Clear index").click().run()
    assert app.session_state["document_auto_sample_disabled"] is True
    assert app.session_state["document_uploader_version"] == 1
    assert not app.exception


def test_analytics_renders_kpis_and_charts():
    app = _app_on("Analytics")
    assert len(app.metric) == 4
    assert any("Start a conversation" in str(item.value) for item in app.info)
    assert not app.exception


def test_training_and_benchmark_actions():
    app = _app_on("Model Training")
    app.button[0].click().run()
    assert len(app.metric) == 4
    assert not app.exception
    next(button for button in app.button if button.label == "Run full benchmark").click().run()
    assert not app.exception
    assert len(app.dataframe) >= 1


def test_all_demo_actions_render():
    app = _app_on("Demo Mode")
    assert len(app.tabs) == 5
    for key in ("btn_nlp", "btn_int", "btn_sent", "btn_coref", "btn_doc"):
        app.button(key=key).click().run()
        assert not app.exception
