"""Customer troubleshooting menu: symptom picker over existing bundles."""

import io

import pytest

from audit import menu


def _driver(lines):
    """Return an input_fn that yields each scripted line in turn."""
    it = iter(lines)
    return lambda _prompt="": next(it)


# --- symptom catalog --------------------------------------------------------

def test_every_symptom_maps_to_a_real_bundle():
    from audit.core import registry
    known = set(registry.bundle_names())
    assert menu.SYMPTOMS, "symptom catalog must not be empty"
    for _label, bundle in menu.SYMPTOMS:
        assert bundle in known, f"{bundle} is not a defined bundle"


# --- the loop ---------------------------------------------------------------

def test_picking_a_symptom_runs_its_bundle_then_quits():
    calls = []
    out = io.StringIO()
    code = menu.run_menu(
        lambda b: (calls.append(b), 2)[1],
        input_fn=_driver(["1", "q"]),
        out=out,
    )
    assert calls == [menu.SYMPTOMS[0][1]]   # first symptom's bundle ran
    assert code == 2                        # exit code propagates from the run
    assert menu.SYMPTOMS[0][0].lower()[:6] in out.getvalue().lower()  # menu rendered


def test_invalid_choice_reprompts_and_runs_nothing():
    calls = []
    out = io.StringIO()
    code = menu.run_menu(
        lambda b: calls.append(b) or 0,
        input_fn=_driver(["banana", "q"]),
        out=out,
    )
    assert calls == []
    assert code == 0
    assert "not a valid" in out.getvalue().lower()


def test_quit_without_running_returns_zero():
    out = io.StringIO()
    code = menu.run_menu(
        lambda b: pytest.fail("should not run a bundle on immediate quit"),
        input_fn=_driver(["q"]),
        out=out,
    )
    assert code == 0


def test_runs_multiple_symptoms_and_returns_worst_exit_code():
    calls = []
    code = menu.run_menu(
        lambda b: (calls.append(b), 2 if b == menu.SYMPTOMS[1][1] else 0)[1],
        input_fn=_driver(["1", "2", "q"]),
        out=io.StringIO(),
    )
    assert calls == [menu.SYMPTOMS[0][1], menu.SYMPTOMS[1][1]]
    assert code == 2   # worst across the session
