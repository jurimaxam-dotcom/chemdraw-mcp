"""OPSIN als Dauer-JVM: einmal starten, Namen zeilenweise über stdin.

py2opsin startet pro Name eine neue JVM (gemessen 1,9–5,8 s je Name). Weil
OPSIN in der Kaskade VOR dem Netz steht, zahlte jeder Trivialname diese Zeit
als Fehlschlag, bevor PubChem in 0,7 s antwortete. Die Dauer-JVM spricht das
CLI-Protokoll, das empirisch geprüft ist (opsin-cli 2.9.0, `-osmi -n`):

- eine Zeile rein, genau eine Zeile raus, pro Zeile geflusht;
- Antwort ist `SMILES\\tName`, bei unparsebarem Namen `\\tName` (Grund auf stderr);
- EOF auf stdin beendet die JVM.

Die Fake-Tests prüfen Wiederverwendung, Neustart, Timeout und Fallback ohne
Java; ein Test gegen die echte JVM prüft, dass das Protokoll so stimmt.
"""

import queue
import time
from unittest.mock import patch

import pytest

from chemdraw_tool import resolver
from chemdraw_tool.resolver import _opsin_lookup

KNOWN = {
    "methane": "C",
    "propan-2-ol": "CC(C)O",
    "butan-1-ol": "CCCCO",
}


class FakeOpsin:
    """Ahmt `java -jar opsin-cli.jar -osmi -n` nach — ohne JVM."""

    def __init__(self, *, mute_after=None, die_after=None, wrong_echo=False):
        self._out = queue.Queue()
        self.stdin = self
        self.stdout = self
        self.written = []
        self.killed = False
        self._mute_after = mute_after
        self._die_after = die_after
        self._wrong_echo = wrong_echo

    # stdin
    def write(self, data):
        for line in data.decode("utf-8").splitlines():
            self.written.append(line)
            n = len(self.written)
            if self._die_after is not None and n > self._die_after:
                self._out.put(b"")
                continue
            if self._mute_after is not None and n > self._mute_after:
                continue
            echo = "something else" if self._wrong_echo and n > 1 else line
            self._out.put(f"{KNOWN.get(line, '')}\t{echo}\n".encode())

    def flush(self):
        pass

    def close(self):
        pass

    # stdout
    def readline(self):
        return self._out.get()

    # Prozess
    def poll(self):
        return 0 if self.killed else None

    def kill(self):
        self.killed = True
        self._out.put(b"")

    terminate = kill

    def wait(self, timeout=None):
        return 0


@pytest.fixture
def fake_jvm():
    """Fake-Popen; jeder Start liefert den nächsten FakeOpsin aus `plan`."""
    spawned = []
    plan = []

    def popen(cmd, **kwargs):
        proc = plan.pop(0) if plan else FakeOpsin()
        if isinstance(proc, Exception):
            raise proc
        spawned.append((cmd, kwargs, proc))
        return proc

    resolver._opsin_reset()
    with (
        patch("chemdraw_tool.resolver._java_runtime_available", return_value=True),
        patch("chemdraw_tool.resolver.shutil.which", return_value="/fake/java"),
        patch("chemdraw_tool.resolver._opsin_jar", return_value="/fake/opsin.jar"),
        patch("chemdraw_tool.resolver.subprocess.Popen", side_effect=popen),
        patch("chemdraw_tool.resolver._opsin_oneshot", return_value=None) as oneshot,
    ):
        yield spawned, plan, oneshot
    resolver._opsin_reset()


def test_two_names_share_one_jvm(fake_jvm):
    spawned, _, oneshot = fake_jvm
    assert _opsin_lookup("propan-2-ol") == "CC(C)O"
    assert _opsin_lookup("butan-1-ol") == "CCCCO"
    assert len(spawned) == 1
    oneshot.assert_not_called()


def test_jvm_is_started_with_absolute_java_and_smiles_plus_name_output(fake_jvm):
    spawned, _, _ = fake_jvm
    _opsin_lookup("propan-2-ol")
    cmd, kwargs, _ = spawned[0]
    assert cmd[0] == "/fake/java"
    assert cmd[-3:] == ["/fake/opsin.jar", "-osmi", "-n"]
    # CWD unter Claude Desktop ist "/" — die JVM darf davon nicht abhängen.
    assert kwargs.get("cwd") not in (None, "/")


def test_unparseable_name_returns_none_and_keeps_the_jvm(fake_jvm):
    spawned, _, oneshot = fake_jvm
    assert _opsin_lookup("Tylenol") is None
    assert _opsin_lookup("propan-2-ol") == "CC(C)O"
    assert len(spawned) == 1
    assert not spawned[0][2].killed
    oneshot.assert_not_called()


def test_dead_jvm_is_replaced_on_next_call(fake_jvm):
    spawned, plan, oneshot = fake_jvm
    plan.append(FakeOpsin(die_after=1))  # Handshake ok, dann EOF
    _opsin_lookup("propan-2-ol")
    oneshot.assert_called_once_with("propan-2-ol")  # dieser Aufruf: alter Weg
    assert _opsin_lookup("butan-1-ol") == "CCCCO"
    assert len(spawned) == 2


def test_mute_jvm_times_out_fast_and_is_killed(fake_jvm, monkeypatch):
    spawned, plan, oneshot = fake_jvm
    monkeypatch.setattr(resolver, "_OPSIN_TIMEOUT", 0.2)
    plan.append(FakeOpsin(mute_after=1))  # Handshake ok, dann Schweigen
    t = time.perf_counter()
    assert _opsin_lookup("propan-2-ol") is None
    assert time.perf_counter() - t < 2
    assert spawned[0][2].killed
    # Ein Hänger wird nicht über py2opsin wiederholt — derselbe Name hinge erneut.
    oneshot.assert_not_called()


def test_echo_mismatch_counts_as_desync(fake_jvm):
    spawned, plan, oneshot = fake_jvm
    plan.append(FakeOpsin(wrong_echo=True))
    _opsin_lookup("propan-2-ol")
    assert spawned[0][2].killed
    oneshot.assert_called_once_with("propan-2-ol")


@pytest.mark.parametrize("name", ["", "   ", "propan-2-ol\nethanol", "ethanol\r"])
def test_name_that_would_break_the_line_protocol_never_reaches_the_pipe(fake_jvm, name):
    spawned, _, oneshot = fake_jvm
    assert _opsin_lookup(name) is None
    for _, _, proc in spawned:
        assert name not in proc.written
    oneshot.assert_not_called()


def test_spawn_failure_falls_back_to_py2opsin(fake_jvm):
    spawned, plan, oneshot = fake_jvm
    plan.append(OSError("no java"))
    oneshot.return_value = "CC(C)O"
    assert _opsin_lookup("propan-2-ol") == "CC(C)O"
    oneshot.assert_called_once_with("propan-2-ol")


def test_persistent_jvm_is_given_up_after_three_failures(fake_jvm):
    spawned, plan, oneshot = fake_jvm
    plan.extend([OSError("1"), OSError("2"), OSError("3")])
    for _ in range(4):
        _opsin_lookup("propan-2-ol")
    assert oneshot.call_count == 4
    assert plan == []  # genau drei Startversuche, der vierte Aufruf startet keine JVM
    assert spawned == []


# --- gegen die echte JVM (braucht eine JRE, wie die übrigen OPSIN-Tests) ------


def test_real_jvm_is_reused_and_answers_unparseable_names():
    resolver._opsin_reset()
    try:
        assert _opsin_lookup("propan-2-ol") is not None
        proc = resolver._opsin_proc
        assert proc is not None
        assert _opsin_lookup("methylphenidate") is None
        assert _opsin_lookup("2-methylbutan-2-ol") is not None
        assert resolver._opsin_proc is proc
    finally:
        resolver._opsin_reset()
