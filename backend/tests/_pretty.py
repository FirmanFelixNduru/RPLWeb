"""
CompareBuy — Formatter output unit test.

Meng-import modul ini mengubah tampilan runner unittest standar menjadi:

    [OK] <deskripsi dari docstring test>
    ...
    === ALL <N> UNIT TESTS PASSED ===

sama gayanya dengan tests/test_api.py. Logika pengujian tidak disentuh.
Jika ada test gagal, tampilan error/traceback standar unittest tetap muncul
(ditambah baris `[FAIL]` / `[ERROR]`), sehingga kegagalan tidak tersembunyi.

Dipakai dengan: `from tests import _pretty  # noqa: F401`
"""
import unittest


def _describe(test) -> str:
    """Deskripsi singkat test: baris pertama docstring, atau nama method yang dirapikan."""
    doc = test.shortDescription()
    if doc:
        return doc.strip().rstrip(".")
    name = getattr(test, "_testMethodName", str(test))
    return name.removeprefix("test_").replace("_", " ")


class _Gate:
    """Pembungkus stream yang bisa membisukan ringkasan bawaan 'Ran N tests ... OK'."""

    def __init__(self, inner):
        self._inner = inner
        self.suppress = False

    def write(self, text):
        if not self.suppress:
            self._inner.write(text)

    def writeln(self, text=None):
        if not self.suppress:
            self._inner.writeln(text)

    def flush(self):
        self._inner.flush()

    def __getattr__(self, name):
        return getattr(self._inner, name)


class PrettyTestResult(unittest.TextTestResult):
    """Satu baris per test: [OK] / [FAIL] / [ERROR] / [SKIP]."""

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        self.stream.writeln(f"[OK] {_describe(test)}")
        self.stream.flush()

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        self.stream.writeln(f"[FAIL] {_describe(test)}")
        self.stream.flush()

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        self.stream.writeln(f"[ERROR] {_describe(test)}")
        self.stream.flush()

    def addSkip(self, test, reason):
        unittest.TestResult.addSkip(self, test, reason)
        self.stream.writeln(f"[SKIP] {_describe(test)} ({reason})")
        self.stream.flush()

    def addExpectedFailure(self, test, err):
        unittest.TestResult.addExpectedFailure(self, test, err)
        self.stream.writeln(f"[XFAIL] {_describe(test)}")
        self.stream.flush()

    def addUnexpectedSuccess(self, test):
        unittest.TestResult.addUnexpectedSuccess(self, test)
        self.stream.writeln(f"[XPASS] {_describe(test)}")
        self.stream.flush()

    def addSubTest(self, test, subtest, err):
        unittest.TestResult.addSubTest(self, test, subtest, err)

    def printErrors(self):
        super().printErrors()
        # Jika semua lulus, bisukan ringkasan 'Ran N tests ... OK' bawaan runner.
        if self.wasSuccessful() and isinstance(self.stream, _Gate):
            self.stream.suppress = True


_original_run = unittest.TextTestRunner.run


def _pretty_run(self, test):
    gate = _Gate(self.stream)
    self.stream = gate
    try:
        result = _original_run(self, test)
    finally:
        gate.suppress = False
        self.stream = gate._inner
    if result.wasSuccessful():
        if result.skipped:
            ran = result.testsRun - sum(1 for t, _ in result.skipped if hasattr(t, "_testMethodName"))
            self.stream.writeln(
                f"=== {ran} UNIT TESTS PASSED, {len(result.skipped)} SKIPPED (BUKAN ALL PASSED) ==="
            )
        else:
            self.stream.writeln(f"=== ALL {result.testsRun} UNIT TESTS PASSED ===")
        self.stream.flush()
    return result


# Idempotent: aman di-import berkali-kali dari banyak file test.
if unittest.TextTestRunner.resultclass is not PrettyTestResult:
    unittest.TextTestRunner.resultclass = PrettyTestResult
    unittest.TextTestRunner.run = _pretty_run
