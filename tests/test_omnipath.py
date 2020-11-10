import pytest

from omnipath import options
from omnipath.constants import License


class TestOptions:
    def test_options_invalid_url_type(self):
        with pytest.raises(TypeError):
            options.url = 42

    def test_options_invalid_url(self):
        with pytest.raises(ValueError):
            options.url = "foo"

    def test_options_url_localhost(self):
        options.url = "https://localhost"

        assert options.url == "https://localhost"

    def test_options_invalid_license(self):
        with pytest.raises(ValueError):
            options.license = "foo"

    def test_options_valid_license(self):
        options.license = "commercial"

        assert isinstance(options.license, License)
        assert options.license == License.COMMERCIAL
