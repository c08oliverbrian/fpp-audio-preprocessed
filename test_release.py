"""Offline release sanity checks without running or modifying a user's FPP/cPanel hosts."""
import ast
import json
import unittest
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_manifest(self):
        cfg = json.loads((ROOT / 'pluginInfo.json').read_text())
        self.assertEqual(cfg['repoName'], 'fpp-audio-preprocessed')
        self.assertTrue(any(float(v['minFPPVersion']) <= 10.3 and v['maxFPPVersion'] == '0'
                            for v in cfg['versions']))
        self.assertIn('privacy', cfg)
        self.assertEqual(cfg['srcURL'], 'https://github.com/c08oliverbrian/fpp-audio-preprocessed.git')

    def test_url_encoded_filenames(self):
        # Regression: some Passenger proxy setups deliver the quoted name directly to Flask.
        name = 'mickey once upon christmas-characters.mp3'
        encoded = quote(name, safe='')
        self.assertEqual(encoded, 'mickey%20once%20upon%20christmas-characters.mp3')
        self.assertEqual(unquote(encoded), name)

    def test_backend_routes_exist(self):
        code = (ROOT / 'backend/cpanel_app.py').read_text()
        for expected in ('/listen/<device>/', '/api/player-config', 'route_media_name(name)',
                         "'donate-qr.png'", 'FPP_DEVELOPER_SUPPORT_ENABLED'):
            self.assertIn(expected, code)
        # Syntax validation without requiring Flask installed on development computer.
        ast.parse(code)

    def test_html_assets(self):
        html = (ROOT / 'web-player/index.html').read_text()
        for name in ('styles.css', 'player.js', 'donate-qr.png'):
            self.assertIn(name, html)
            self.assertTrue((ROOT / 'web-player' / name).is_file())
        self.assertIn('software developer', html.lower())

    def test_token_not_disclosed_in_public_player_config(self):
        src = (ROOT / 'backend/cpanel_app.py').read_text()
        block = src.split('def player_config():', 1)[1].split('@app.', 1)[0]
        self.assertNotIn("'FPP_STREAM_TOKEN'", block)
        self.assertNotIn("'FPP_PAIR_CODE'", block)
        self.assertIn('publishable_key', block)

    def test_no_private_material_in_bundle(self):
        forbidden = ['sk_live_', '-----BEGIN PRIVATE KEY-----', 'password =', 'pk_test_']
        for suffix in ('.py', '.php', '.js', '.json'):
            for path in ROOT.rglob('*' + suffix):
                if '/tests/' in str(path):
                    continue
                text = path.read_text(errors='replace')
                for fragment in forbidden:
                    self.assertNotIn(fragment, text, f'Bad secret-like content: {path}')


if __name__ == '__main__':
    unittest.main()
