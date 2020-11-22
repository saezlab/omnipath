from os import remove
from typing import Optional
from pathlib import Path
from configparser import NoSectionError

import pytest

from omnipath.constants import License
from omnipath._core.utils._options import Options
from omnipath.constants._pkg_constants import DEFAULT_OPTIONS


class TestOptions:
    def test_invalid_url_type(self, options: Options):
        with pytest.raises(TypeError):
            options.url = 42

    def test_invalid_url(self, options: Options):
        with pytest.raises(ValueError):
            options.url = "foo"

    def test_invalid_license(self, options: Options):
        with pytest.raises(ValueError):
            options.license = "foo"

    def test_invalid_cache_type(self, options: Options):
        with pytest.raises(TypeError):
            options.cache = 42

    def test_invalid_password_type(self, options: Options):
        with pytest.raises(TypeError):
            options.password = 42

    def test_invalid_num_retries(self, options: Options):
        with pytest.raises(ValueError):
            options.num_retries = -1

    def test_invalid_timeout(self, options: Options):
        with pytest.raises(ValueError):
            options.timeout = 0

    def test_invalid_chunk_size(self, options: Options):
        with pytest.raises(ValueError):
            options.chunk_size = 0

    def test_from_options_invalid_type(self):
        with pytest.raises(TypeError):
            Options.from_options("foo")

    def test_url_localhost(self, options: Options):
        options.url = "https://localhost"

        assert options.url == "https://localhost"

    @pytest.mark.parametrize("license", list(License))
    def test_valid_license(self, options: Options, license: License):
        options.license = license.value

        assert isinstance(options.license, License)
        assert options.license == license

    @pytest.mark.parametrize("pwd", ["foo", None])
    def test_password(self, options: Options, pwd: Optional[str]):
        options.password = pwd

        assert options.password == pwd

    def test_from_options(self, options: Options):
        new_opt = Options.from_options(options)

        for k, v in options.__dict__.items():
            assert getattr(new_opt, k) == v

    def test_from_options_new_values(self, options: Options):
        new_opt = Options.from_options(
            options, autoload=not options.autoload, num_retries=0
        )

        for k, v in options.__dict__.items():
            if k not in ("autoload", "num_retries"):
                assert getattr(new_opt, k) == v

        assert new_opt.autoload != options.autoload
        assert new_opt.num_retries == 0

    def test_from_config_no_file(self, config_backup):
        if Path(Options.config_path).exists():
            remove(Options.config_path)

        new_opt = Options.from_config()

        for k, v in DEFAULT_OPTIONS.__dict__.items():
            if hasattr(new_opt, k) and not k.startswith("_"):
                assert getattr(new_opt, k) == v

    def test_from_config_section_is_not_url(self):
        with pytest.raises(NoSectionError, match=r"No section: 'http://foo.bar'"):
            Options.from_config("http://foo.bar")

    def test_write_config(self, options: Options, config_backup):
        options.timeout = 1337
        options.license = License.COMMERCIAL
        options.password = "foobarbaz"
        options.write()

        new_opt = Options.from_config()
        for k, v in options.__dict__.items():
            if k == "cache":
                assert type(new_opt.cache) == type(options.cache)  # noqa: E721
            elif k == "password":
                # don't store the password in the file
                assert getattr(new_opt, k) is None
            elif k not in ("timeout", "license"):
                assert getattr(new_opt, k) == v

        assert new_opt.timeout == 1337
        assert new_opt.license == License.COMMERCIAL

    def test_write_new_section(self, options: Options, config_backup):
        options.timeout = 42
        options.write("https://foo.bar")

        new_opt = Options.from_config("https://foo.bar")
        assert options is not new_opt
        for k, v in options.__dict__.items():
            if k == "url":
                assert v == options.url
                assert new_opt.url == "https://foo.bar"
            elif k == "cache":
                assert type(new_opt.cache) == type(options.cache)  # noqa: E721
            else:
                assert getattr(new_opt, k) == v

    def test_write_new_section_not_url(self, options: Options, config_backup):
        with pytest.raises(ValueError, match=r"Invalid URL: `foobar`."):
            options.write("foobar")

    def test_contextmanager(self, options: Options):
        with options as new_opt:
            assert options is not new_opt
            for k, v in options.__dict__.items():
                if k == "cache":
                    assert type(new_opt.cache) == type(options.cache)  # noqa: E721
                else:
                    assert getattr(new_opt, k) == v
