from nose.tools import assert_raises
import textwrap
from StringIO import StringIO
from test.test_support import check_warnings
from webassets.loaders import YAMLLoader, LoaderError
from nose import SkipTest


class TestYAML(object):

    def setup(self):
        try:
            import yaml
        except ImportError:
            raise SkipTest()

    def loader(self, text, filename=None):
        io = StringIO(textwrap.dedent(text))
        if filename:
            io.name = filename
        return YAMLLoader(io)

    def test_load_bundles(self):
        bundles = self.loader("""
        standard:
            filters: cssmin,gzip
            output: output.css
            contents:
                - file1
                - file2
        empty-bundle:
        single-content-as-string-bundle:
            contents: only-this
        """).load_bundles()

        assert len(bundles) == 3
        assert bundles['standard'].output == 'output.css'
        assert len(bundles['standard'].filters) == 2
        assert bundles['standard'].contents == ('file1', 'file2')
        assert bundles['empty-bundle'].contents == ()
        assert bundles['single-content-as-string-bundle'].contents == ('only-this',)

    def test_empty_files(self):
        """YAML loader can deal with empty files.
        """
        self.loader("""""").load_bundles()
        # A LoaderError is what we expect here, rather than, say, a TypeError.
        assert_raises(LoaderError, self.loader("""""").load_environment)

    def test_load_environment_error(self):
        """Check that "url" and "directory" are required.
        """
        assert_raises(LoaderError, self.loader("""
        url: /foo
        """).load_environment)
        assert_raises(LoaderError, self.loader("""
        directory: bar
        """).load_environment)

    def test_load_environment(self):
        environment = self.loader("""
        url: /foo
        directory: something
        versioner: 'timestamp'
        auto_build: true
        url_expire: true

        bundles:
            test:
                output: foo
        """).load_environment()
        assert environment.url == '/foo'
        assert environment.url_expire == True
        assert environment.auto_build == True
        assert environment.config['versioner'] == 'timestamp'

        # Because the loader isn't aware of the file location, the
        # directory is read as-is, relative to cwd rather than the
        # file location.
        assert environment.directory == 'something'

        # [bug] Make sure the bundles are loaded as well.
        assert len(environment) == 1

    def test_load_deprecated_attrs(self):
        with check_warnings(("", DeprecationWarning)) as w:
            environment = self.loader("""
            url: /foo
            directory: something
            updater: false
            """).load_environment()
            assert environment.auto_build == False

    def test_load_environment_directory_base(self):
        environment = self.loader("""
        url: /foo
        directory: ../something
        """, filename='/var/www/project/config/yaml').load_environment()
        # The directory is considered relative to the YAML file location.
        print environment.directory
        assert environment.directory == '/var/www/project/something'
