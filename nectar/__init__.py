from __future__ import print_function
from six.moves import urllib

import contextlib
import datetime
import errno
import glob
import json
import os
import platform
import shutil
import subprocess


class BadVersion (Exception):
    pass

class NonEmptyDirWarning (Exception):
    pass

class VersionManager (object):
    VERSIONS = {
        'erlang': [
            ('17.5',   'https://github.com/erlang/otp/archive/OTP-17.5.tar.gz'),
            ('17.5.1', 'https://github.com/erlang/otp/archive/OTP-17.5.1.tar.gz'),
            ('17.5.2', 'https://github.com/erlang/otp/archive/OTP-17.5.2.tar.gz'),
            ('17.5.3', 'https://github.com/erlang/otp/archive/OTP-17.5.3.tar.gz'),
            ('17.5.4', 'https://github.com/erlang/otp/archive/OTP-17.5.4.tar.gz'),
            ('17.5.5', 'https://github.com/erlang/otp/archive/OTP-17.5.5.tar.gz'),
            ('17.5.6', 'https://github.com/erlang/otp/archive/OTP-17.5.6.tar.gz'),
            ('18.0', 'https://github.com/erlang/otp/archive/OTP-18.0.tar.gz'),
            ('18.0.1', 'https://github.com/erlang/otp/archive/OTP-18.0.1.tar.gz'),
            ('18.0.2', 'https://github.com/erlang/otp/archive/OTP-18.0.2.tar.gz'),
            ('18.0.3', 'https://github.com/erlang/otp/archive/OTP-18.0.3.tar.gz'),
            ('18.1', 'https://github.com/erlang/otp/archive/OTP-18.1.tar.gz'),
            ('18.2', 'https://github.com/erlang/otp/archive/OTP-18.2.tar.gz'),
            ('18.2.1', 'https://github.com/erlang/otp/archive/OTP-18.2.1.tar.gz'),
            ('18.2.2', 'https://github.com/erlang/otp/archive/OTP-18.2.2.tar.gz'),
            ('19.0.5', 'https://github.com/erlang/otp/archive/OTP-19.0.5.tar.gz'),
        ],

        'elixir': [
            ('1.0.0', 'https://github.com/elixir-lang/elixir/archive/v1.0.0.tar.gz'),
            ('1.0.1', 'https://github.com/elixir-lang/elixir/archive/v1.0.1.tar.gz'),
            ('1.0.2', 'https://github.com/elixir-lang/elixir/archive/v1.0.2.tar.gz'),
            ('1.0.3', 'https://github.com/elixir-lang/elixir/archive/v1.0.3.tar.gz'),
            ('1.0.4', 'https://github.com/elixir-lang/elixir/archive/v1.0.4.tar.gz'),
            ('1.0.5', 'https://github.com/elixir-lang/elixir/archive/v1.0.5.tar.gz'),
            ('1.1.0', 'https://github.com/elixir-lang/elixir/archive/v1.1.0.tar.gz'),
            ('1.2.0', 'https://github.com/elixir-lang/elixir/archive/v1.2.0.tar.gz'),
            ('1.2.1', 'https://github.com/elixir-lang/elixir/archive/v1.2.1.tar.gz'),
            ('1.3.2', 'https://github.com/elixir-lang/elixir/archive/v1.3.2.tar.gz'),
        ]
    }

    OTP_LATEST = VERSIONS['erlang'][-1][0]
    EX_LATEST = VERSIONS['elixir'][-1][0]

    HOME = os.path.join(os.path.expanduser('~'), '.nectar')

    def __init__(self):
        self._make_nectar_dir()
        self.dnlds = os.path.join(self.HOME, 'downloads')
        self.build = os.path.join(self.HOME, 'build')
        self.bin = os.path.join(self.HOME, 'bin')
        self.logs = os.path.join(self.HOME, 'logs')
        self.logfile = os.path.join(self.logs, datetime.datetime.now().isoformat() + '.log')
        self.otpver, self.exver = self._read_version_file()
        self.make = self._which_make()

    def set_executable_links(self, otpver, exver):
        self._check_versions(otp=otpver, ex=exver)
        with self._change_directory(self.bin):
            self._symlink_executables(os.path.join(self.build, otpver, 'local', 'bin'))
            self._symlink_executables(os.path.join(self.build, otpver, exver, 'local', 'bin'))
        self._write_version_file(otpver, exver)

    def list_versions(self):
        print(' \tERLANG\t|\tELIXIR')
        print(' \t------\t|\t------')
        otpvers = set(map(lambda x: x[0], self.VERSIONS['erlang']))
        exvers = set(map(lambda x: x[0], self.VERSIONS['elixir']))
        for otp_path in sorted(glob.glob(os.path.join(self.build, '*'))):
            otpver = os.path.basename(otp_path)
            if otpver in otpvers:
                for elixir in sorted(glob.glob(os.path.join(otp_path, '*'))):
                    exver = os.path.basename(elixir)
                    if exver in exvers:
                        if exver == self.exver and otpver == self.otpver:
                            flag = '*'
                        else:
                            flag = ' '
                        print('%s\t%s\t|\t%s' % (flag, otpver, exver))

    ## ERLANG METHODS

    def download_erlang(self, version=OTP_LATEST):
        self._check_versions(otp=version)
        return self._download('erlang', version)

    def build_erlang(self, version, jobs):
        self._check_versions(otp=version)

        # make directories
        outdir = os.path.join(self.build, version)
        self._mkdir(outdir)
        self._mkdir(outdir, 'local')

        # return if Erlang has already been installed
        if glob.glob(os.path.join(outdir, 'local', '*')):
            return

        # untar and make
        tarfile = os.path.join(self.dnlds, 'otp-OTP-' + version + '.tar.gz')
        build_dir = os.path.join(outdir, 'otp-OTP-' + version)
        prefix_path = os.path.join(outdir, 'local')
        print('Extracting erlang %s...' % version)
        self._run('tar', 'xzvf', tarfile, '--directory', outdir)
        print('Building erlang %s -- this may take some time...' % version)
        with self._change_directory(build_dir):
            os.environ['ERL_TOP'] = build_dir
            self._run('./otp_build', 'autoconf')
            self._run('./configure', '--prefix=%s' % prefix_path)
            self._run(self.make, '-j%d' % jobs)
            self._run(self.make, 'install')

    def remove_erlang(self, version, force=False, purge=False):
        self._check_versions(otp=version)
        otp_path = os.path.join(self.build, version)
        if not os.path.exists(otp_path):
            raise BadVersion('erlang %s is not installed' % version)
        if not force:
            elixirs = set(map(lambda x: x[0], self.VERSIONS['elixir']))
            for elixir in glob.glob(os.path.join(otp_path, '*')):
                if os.path.basename(elixir) in elixirs:
                    raise NonEmptyDirWarning('Are you sure you want to remove '
                            'OTP %s and all its dependents?' % version)

        shutil.rmtree(otp_path)
        if purge:
            outfile, _ = self._interpret_version('erlang', version)
            os.remove(outfile)

    ## ELIXIR METHODS

    def download_elixir(self, version=EX_LATEST):
        self._check_versions(ex=version)
        return self._download('elixir', version)

    def build_elixir(self, version, otp_version, jobs):
        self._check_versions(otp=otp_version, ex=version)
        self._ensure_erlang(otp_version, jobs)

        # make directories
        outdir = os.path.join(self.build, otp_version, version)
        self._mkdir(outdir)
        self._mkdir(outdir, 'local')
        self._mkdir(outdir, 'local', 'bin')

        # return if Elixir has already been installed
        if glob.glob(os.path.join(outdir, 'local', 'bin', '*')):
            return

        # untar and make
        tarfile = os.path.join(self.dnlds, 'elixir-' + version + '.tar.gz')
        print('Extracting elixir %s...' % version)
        self._run('tar', 'xzvf', tarfile, '--directory', outdir)
        print('Building elixir %s -- this may take some time...' % version)
        build_dir = os.path.join(outdir, 'elixir-' + version)
        otp_path = os.path.join(self.build, otp_version, 'local', 'bin')
        with self._change_directory(build_dir):
            os.environ['PATH'] = otp_path + ':' + os.environ['PATH']
            self._run(self.make, '-j%d' % jobs)

        # install
        with self._change_directory(os.path.join(outdir, 'local', 'bin')):
            for tool in ('elixir', 'elixirc', 'iex', 'mix'):
                os.symlink(os.path.join(build_dir, 'bin', tool), tool)

    def remove_elixir(self, version, otp_version, purge=False):
        self._check_versions(otp=otp_version, ex=version)
        otp_path = os.path.join(self.build, otp_version)
        if not os.path.exists(otp_path):
            raise BadVersion('erlang %s is not installed' % otp_version)
        ex_path = os.path.join(otp_path, version)
        if not os.path.exists(ex_path):
            raise BadVersion('elixir %s is not installed' % version)
        shutil.rmtree(os.path.join(self.build, otp_version, version))
        if purge:
            outfile, _ = self._interpret_version('elixir', version)
            os.remove(outfile)

    ## PRIVATE

    def _mkdir(self, *dirs):
        try:
            os.mkdir(os.path.join(*dirs))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    def _run(self, *command):
        with open(self.logfile, 'a') as log:
            print(' '.join(command), file=log)
            log.flush()
            subprocess.check_call(command, stdout=log, stderr=log)

    def _which_make(self):
        if platform.system() == 'FreeBSD':
            return 'gmake'
        else:
            return 'make'

    def _symlink_executables(self, directory):
        for exe in glob.glob(os.path.join(directory, '*')):
            name = os.path.basename(exe)
            if os.path.islink(name):
                os.remove(name)
            os.symlink(exe, name)

    def _make_nectar_dir(self):
        self._mkdir(self.HOME)
        self._mkdir(self.HOME, 'downloads')
        self._mkdir(self.HOME, 'build')
        self._mkdir(self.HOME, 'bin')
        self._mkdir(self.HOME, 'logs')

    def _read_version_file(self):
        version_file = os.path.join(self.HOME, 'version.json')
        try:
            with open(version_file, 'r') as f:
                result = json.load(f)
            return result['erlang'], result['elixir']

        except IOError:
            return None, None

    def _write_version_file(self, erlang, elixir):
        version_file = os.path.join(self.HOME, 'version.json')
        with open(version_file, 'w') as f:
            json.dump({'erlang': erlang, 'elixir': elixir}, f)

    def _interpret_version(self, tool, version):
        res = list(filter(lambda x: x[0] == version, self.VERSIONS[tool]))
        if not res:
            raise BadVersion('%s %s is not valid' % (tool, version))

        version, url = res[0]
        if tool == 'erlang':
            tarfile = 'otp-OTP-' + version + '.tar.gz'
        else:
            tarfile = 'elixir-' + version + '.tar.gz'
        return os.path.join(self.dnlds, tarfile), url

    def _download(self, tool, version):
        outfile, url = self._interpret_version(tool, version)
        if os.path.isfile(outfile):
            return outfile

        print('Downloading %s %s...' % (tool, version))
        if platform.system() == 'FreeBSD':
            response = urllib.request.urlopen(url, cafile='/usr/local/share/certs/ca-root-nss.crt')
        else:
            response = urllib.request.urlopen(url)

        with open(outfile, 'wb') as f:
            f.write(response.read())
        return outfile

    @contextlib.contextmanager
    def _change_directory(self, new_dir):
        prev = os.getcwd()
        os.chdir(new_dir)
        try:
            yield
        finally:
            os.chdir(prev)

    def _ensure_erlang(self, version, jobs):
        self.download_erlang(version)
        self.build_erlang(version, jobs)

    def _check_versions(self, otp=OTP_LATEST, ex=EX_LATEST):
        if otp not in list(map(lambda x: x[0], self.VERSIONS['erlang'])):
            raise BadVersion('erlang %s is not valid' % otp)
        if ex not in list(map(lambda x: x[0], self.VERSIONS['elixir'])):
            raise BadVersion('elixir %s is not valid' % ex)
