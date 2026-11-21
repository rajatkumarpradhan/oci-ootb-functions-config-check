import unittest

from fn_check.model import Application, Function
from fn_check.rules import (
    exit_code,
    rule_default_memory,
    rule_default_timeout,
    rule_empty_application,
    rule_secret_config,
    run_all,
)


def fn(name="f", labels=("prod",), timeout=60, memory=256, config=()):
    return Function(name=name, labels=tuple(labels), timeout=timeout, memory=memory, config=tuple(config))


def app(name="a", functions=(fn(),)):
    return Application(name=name, functions=tuple(functions))


class TestFnc001(unittest.TestCase):
    def test_fires_secret_key(self):
        out = rule_secret_config((app(functions=(fn(config=(("DB_PASSWORD", "x"),)),)),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_fires_token_key(self):
        out = rule_secret_config((app(functions=(fn(config=(("AUTH_TOKEN", "t"),)),)),))
        self.assertIn("AUTH_TOKEN", out[0].detail)

    def test_quiet_empty_value(self):
        self.assertEqual(rule_secret_config((app(functions=(fn(config=(("DB_PASSWORD", ""),)),)),)), [])

    def test_quiet_normal_config(self):
        self.assertEqual(rule_secret_config((app(),)), [])


class TestFnc002(unittest.TestCase):
    def test_fires_prod_no_timeout(self):
        out = rule_default_timeout((app(functions=(fn(timeout=None),)),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_quiet_prod_with_timeout(self):
        self.assertEqual(rule_default_timeout((app(),)), [])

    def test_quiet_dev_no_timeout(self):
        self.assertEqual(rule_default_timeout((app(functions=(fn(labels=("dev",), timeout=None),)),)), [])


class TestFnc003(unittest.TestCase):
    def test_fires_prod_no_memory(self):
        out = rule_default_memory((app(functions=(fn(memory=None),)),))
        self.assertEqual(len(out), 1)

    def test_quiet_prod_with_memory(self):
        self.assertEqual(rule_default_memory((app(),)), [])

    def test_quiet_dev_no_memory(self):
        self.assertEqual(rule_default_memory((app(functions=(fn(labels=("dev",), memory=None),)),)), [])


class TestFnc004(unittest.TestCase):
    def test_fires_empty_app(self):
        out = rule_empty_application((app(functions=()),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_quiet_nonempty(self):
        self.assertEqual(rule_empty_application((app(),)), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((app(functions=(fn(config=(("APP_SECRET", "x"),)),)),))), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((app(functions=(fn(timeout=None),)),))), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((app(),))), 0)


if __name__ == "__main__":
    unittest.main()
