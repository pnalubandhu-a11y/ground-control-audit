"""Customer troubleshooting menu: symptom picker + post-verdict action menu."""

import io

import pytest

from audit import menu


def _driver(lines):
    """Return an input_fn that yields each scripted line in turn."""
    it = iter(lines)
    return lambda _prompt="": next(it)


class FakeOutcome:
    """Stand-in for a completed run, as returned by the run_bundle callback."""

    def __init__(self, code, *, bundle_path="audit-bundle-host-x.tar.gz",
                 evidence="EVIDENCE-DUMP"):
        self.exit_code = code
        self._bundle_path = bundle_path
        self._evidence = evidence
        self.bundle_calls = 0
        self.evidence_calls = 0

    def support_bundle(self):
        self.bundle_calls += 1
        return self._bundle_path

    def evidence(self):
        self.evidence_calls += 1
        return self._evidence


# --- symptom catalog --------------------------------------------------------

def test_every_symptom_maps_to_a_real_bundle():
    from audit.core import registry
    known = set(registry.bundle_names())
    assert menu.SYMPTOMS, "symptom catalog must not be empty"
    for _label, bundle in menu.SYMPTOMS:
        assert bundle in known, f"{bundle} is not a defined bundle"


# --- the picker loop --------------------------------------------------------

def test_picking_a_symptom_runs_its_bundle_then_quits():
    calls = []
    out = io.StringIO()
    # pick 1 -> run -> [Enter] back -> q
    code = menu.run_menu(
        lambda b: (calls.append(b), FakeOutcome(2))[1],
        input_fn=_driver(["1", "", "q"]),
        out=out,
    )
    assert calls == [menu.SYMPTOMS[0][1]]
    assert code == 2
    assert menu.SYMPTOMS[0][0].lower()[:6] in out.getvalue().lower()


def test_invalid_choice_reprompts_and_runs_nothing():
    calls = []
    out = io.StringIO()
    code = menu.run_menu(
        lambda b: calls.append(b) or FakeOutcome(0),
        input_fn=_driver(["banana", "q"]),
        out=out,
    )
    assert calls == []
    assert code == 0
    assert "not a valid" in out.getvalue().lower()


def test_quit_without_running_returns_zero():
    code = menu.run_menu(
        lambda b: pytest.fail("should not run a bundle on immediate quit"),
        input_fn=_driver(["q"]),
        out=io.StringIO(),
    )
    assert code == 0


def test_runs_multiple_symptoms_and_returns_worst_exit_code():
    calls = []
    code = menu.run_menu(
        lambda b: (calls.append(b),
                   FakeOutcome(2 if b == menu.SYMPTOMS[1][1] else 0))[1],
        input_fn=_driver(["1", "", "2", "", "q"]),
        out=io.StringIO(),
    )
    assert calls == [menu.SYMPTOMS[0][1], menu.SYMPTOMS[1][1]]
    assert code == 2


# --- the post-verdict action menu -------------------------------------------

def test_support_action_writes_bundle():
    outcome = FakeOutcome(2)
    out = io.StringIO()
    # pick 1 -> [s] package -> [Enter] back -> q
    menu.run_menu(lambda b: outcome, input_fn=_driver(["1", "s", "", "q"]), out=out)
    assert outcome.bundle_calls == 1
    assert "audit-bundle-host-x.tar.gz" in out.getvalue()


def test_evidence_action_prints_evidence():
    outcome = FakeOutcome(2)
    out = io.StringIO()
    menu.run_menu(lambda b: outcome, input_fn=_driver(["1", "v", "", "q"]), out=out)
    assert outcome.evidence_calls == 1
    assert "EVIDENCE-DUMP" in out.getvalue()


def test_enter_returns_to_menu_without_any_action():
    outcome = FakeOutcome(0)
    menu.run_menu(lambda b: outcome, input_fn=_driver(["1", "", "q"]), out=io.StringIO())
    assert outcome.bundle_calls == 0
    assert outcome.evidence_calls == 0


def test_invalid_action_reprompts():
    outcome = FakeOutcome(0)
    out = io.StringIO()
    # pick 1 -> bogus action -> [Enter] back -> q
    menu.run_menu(lambda b: outcome, input_fn=_driver(["1", "zzz", "", "q"]), out=out)
    assert outcome.bundle_calls == 0
    assert outcome.evidence_calls == 0
    assert "[s]" in out.getvalue() and "[v]" in out.getvalue()
