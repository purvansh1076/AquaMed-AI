from app.ml.shadow_mode import ShadowState


def test_shadow_states():
    assert ShadowState.CREATED.value == "CREATED"
    assert len(list(ShadowState)) == 7
