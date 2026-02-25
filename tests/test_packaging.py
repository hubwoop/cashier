"""
Tests for project packaging: setup.py and requirements.txt.
"""

import ast
import re


class TestSetupPy:
    """Verify setup.py is correctly configured."""

    def _parse_setup_kwargs(self):
        """Parse setup() keyword arguments from setup.py using AST."""
        with open('setup.py', 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'setup':
                kwargs = {}
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Constant):
                        kwargs[kw.arg] = kw.value.value
                    elif isinstance(kw.value, ast.List):
                        kwargs[kw.arg] = [
                            elt.value if isinstance(elt, ast.Constant) else str(elt)
                            for elt in kw.value.elts
                        ]
                return kwargs
        return {}

    def test_install_requires_does_not_self_reference(self):
        """setup.py must NOT list 'cashier' as its own dependency."""
        kwargs = self._parse_setup_kwargs()
        deps = kwargs.get('install_requires', [])
        for dep in deps:
            # Strip version specifier before comparing
            name = re.split(r'[><=!]', dep)[0].strip().lower()
            assert name != 'cashier', (
                f"Circular dependency: setup.py lists '{dep}' as a dependency of itself"
            )

    def test_install_requires_includes_flask(self):
        """Flask must be listed as a dependency."""
        kwargs = self._parse_setup_kwargs()
        deps = [d.lower() for d in kwargs.get('install_requires', [])]
        assert any('flask' in d for d in deps), "Flask not found in install_requires"

    def test_name_is_cashier(self):
        kwargs = self._parse_setup_kwargs()
        assert kwargs.get('name') == 'cashier'


class TestRequirementsTxt:
    """Verify requirements.txt has sensible version bounds."""

    def _read_requirements(self):
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def test_flask_version_minimum_is_modern(self):
        """Flask minimum version should be at least 2.0 (not the ancient 0.12)."""
        reqs = self._read_requirements()
        for req in reqs:
            if req.lower().startswith('flask'):
                # Extract version number after >= or ==
                match = re.search(r'>=\s*([\d.]+)', req)
                if match:
                    major = int(match.group(1).split('.')[0])
                    assert major >= 2, f"Flask minimum version too old: {req}"
                break
        else:
            assert False, "Flask not found in requirements.txt"
