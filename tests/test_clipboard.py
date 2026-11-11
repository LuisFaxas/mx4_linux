"""Copy / paste keys per focused app.

    python3 -m unittest discover tests
"""

import unittest

from mx4.clipboard import kind_for


class Kinds(unittest.TestCase):
    def test_terminals(self):
        for focus in ("org.gnome.ptyxis org.gnome.ptyxis.desktop", "herdr-app herdr-app.desktop",
                      "org.gnome.console org.gnome.console.desktop", "kitty kitty.desktop"):
            self.assertEqual(kind_for(focus), "terminal", focus)

    def test_vscode_gets_the_insert_keys(self):
        self.assertEqual(kind_for("code code.desktop"), "insert")
        # the Microsoft build, as GNOME 51 reports it
        self.assertEqual(kind_for("com.microsoft.vscode com.microsoft.vscode.desktop"), "insert")

    def test_other_apps_are_plain(self):
        for focus in ("firefox org.mozilla.firefox.desktop", "telegramdesktop org.telegram.desktop.desktop",
                      "org.gnome.nautilus org.gnome.nautilus.desktop"):
            self.assertEqual(kind_for(focus), "plain", focus)

    def test_word_match_not_substring(self):
        # "code" must not catch an app that merely contains the letters
        self.assertEqual(kind_for("org.gnome.decoder decoder.desktop"), "plain")

    def test_unknown_focus_is_safe(self):
        self.assertEqual(kind_for(None), "insert")
        self.assertEqual(kind_for(""), "plain")


if __name__ == "__main__":
    unittest.main()
