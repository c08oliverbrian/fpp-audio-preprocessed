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
                         "'donate-qr.png'", "'enabled': True"):
            self.assertIn(expected, code)
        # Syntax validation without requiring Flask installed on development computer.
        ast.parse(code)

    def test_html_assets(self):
        html = (ROOT / 'web-player/index.html').read_text()
        for name in ('styles.css', 'player.js', 'donate-qr.png'):
            self.assertIn(name, html)
            self.assertTrue((ROOT / 'web-player' / name).is_file())
        self.assertIn('software developer', html.lower())

    def test_public_show_title_masks_device_id(self):
        js = (ROOT / 'web-player/player.js').read_text()
        self.assertIn("const publicShowName = state =>", js)
        self.assertIn("ids.includes(title.toLowerCase())", js)
        self.assertIn("$('show').textContent = publicShowName(state);", js)

    def test_simplified_player(self):
        html = (ROOT / 'web-player/index.html').read_text()
        self.assertNotIn('Enjoy the music while you watch the display.', html)
        self.assertNotIn('class="artwork"', html)
        css = (ROOT / 'web-player/styles.css').read_text()
        self.assertNotIn('.artwork{', css)
        self.assertIn('LIGHTSHOW<span class="wordmark-accent">WEB STREAM', html)

    def test_manual_and_renaming(self):
        manual = ROOT / 'docs/USER-MANUAL.md'
        self.assertTrue(manual.is_file())
        php = (ROOT / 'content.php').read_text()
        self.assertIn('https://github.com/c08oliverbrian/fpp-audio-preprocessed/blob/main/docs/USER-MANUAL.md', php)
        self.assertIn('Instructions manual', php)
        for file in [ROOT / 'README.md', ROOT / 'pluginInfo.json', ROOT / 'content_menu.inc', ROOT / 'web-player/index.html']:
            self.assertNotIn('LightShow Radio', file.read_text())

    def test_token_not_disclosed_in_public_player_config(self):
        src = (ROOT / 'backend/cpanel_app.py').read_text()
        block = src.split('def player_config():', 1)[1].split('@app.', 1)[0]
        self.assertNotIn("'FPP_STREAM_TOKEN'", block)
        self.assertNotIn("'FPP_PAIR_CODE'", block)
        self.assertIn("'enabled': True", block)
        self.assertNotIn('FPP_DEVELOPER_SUPPORT_ENABLED', src)

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

class ConfigurationPermissionsTests(unittest.TestCase):
    def test_php_and_agent_can_both_access_settings(self):
        hook = (ROOT/'scripts/fpp_install.sh').read_text()
        self.assertIn('WEB_GROUP=www-data', hook)
        self.assertIn('chmod 660 "$CFG"', hook)
        self.assertIn("legacy.get('token')", hook)

    def test_no_server_side_support_disable(self):
        for path in (ROOT/'backend/cpanel_app.py',ROOT/'backend/.env.example'):
            self.assertNotIn('FPP_DEVELOPER_SUPPORT_ENABLED',path.read_text())

class CatalogReviewTests(unittest.TestCase):
    def test_hooks_are_executable(self):
        for path in ('fpp_install.sh','fpp_uninstall.sh','scripts/fpp_install.sh','scripts/fpp_uninstall.sh'):
            self.assertTrue((ROOT/path).stat().st_mode & 0o111, path)

    def test_sudo_not_in_install_hooks(self):
        for path in ('fpp_install.sh','fpp_uninstall.sh','scripts/fpp_install.sh','scripts/fpp_uninstall.sh'):
            self.assertNotIn('sudo ', (ROOT/path).read_text())

    def test_private_config_and_log(self):
        self.assertIn('/home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json', (ROOT/'agent/agent.py').read_text())
        self.assertIn('/home/fpp/media/plugindata/fpp-audio-preprocessed/settings.json', (ROOT/'content.php').read_text())
        self.assertIn('/home/fpp/media/logs/plugin-fpp-audio-preprocessed.log', (ROOT/'agent/agent.py').read_text())
        self.assertIn('systemctl disable --now fpp-audio-preprocessed.service', (ROOT/'scripts/fpp_uninstall.sh').read_text())

    def test_privacy_and_csp(self):
        m=json.loads((ROOT/'pluginInfo.json').read_text())
        self.assertEqual(m['releaseNotesStyle'],'gitHistory')
        self.assertLessEqual(len(m['privacy']['summary']),200)
        recipients={x['to'] for x in m['privacy']['sends']}
        self.assertIn('donate.stripe.com',recipients)
        self.assertIn('buy.stripe.com',recipients)
        self.assertTrue(any(s['kind']=='service' and 'fpp-audio-preprocessed' in s['what'] for s in m['privacy']['systemChanges']))
        self.assertNotIn('js.stripe.com', (ROOT/'web-player/player.js').read_text())


class RepeatSaveRegressionTests(unittest.TestCase):
    def test_php_does_not_revoke_web_server_access_after_save(self):
        php = (ROOT / 'content.php').read_text()
        self.assertIn('file_put_contents($path', php)
        self.assertNotIn('@chmod($path, 0600)', php)
        self.assertNotIn('chmod($path, 0600)', php)
        self.assertIn('installer-managed 0660 mode', php)

    def test_install_hook_repairs_existing_permissions(self):
        hook = (ROOT / 'scripts/fpp_install.sh').read_text()
        self.assertIn('chown fpp:"$WEB_GROUP" "$CFG"', hook)
        self.assertIn('chmod 660 "$CFG"', hook)
        self.assertIn('install -d -o fpp -g "$WEB_GROUP" -m 2770 "$DATA_DIR"', hook)
