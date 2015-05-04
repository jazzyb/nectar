#!/usr/bin/env python

from __future__ import print_function

import contextlib
import errno
import glob
import json
import os
import subprocess
import urllib2

class Nectar (object):
    VERSIONS = {
        'erlang': [
            ('17.3',   'https://github.com/erlang/otp/archive/OTP-17.3.tar.gz'),
            ('17.3.1', 'https://github.com/erlang/otp/archive/OTP-17.3.1.tar.gz'),
            ('17.3.2', 'https://github.com/erlang/otp/archive/OTP-17.3.2.tar.gz'),
            ('17.3.3', 'https://github.com/erlang/otp/archive/OTP-17.3.3.tar.gz'),
            ('17.3.4', 'https://github.com/erlang/otp/archive/OTP-17.3.4.tar.gz'),
            ('17.4',   'https://github.com/erlang/otp/archive/OTP-17.4.tar.gz'),
            ('17.4.1', 'https://github.com/erlang/otp/archive/OTP-17.4.1.tar.gz'),
            ('17.5',   'https://github.com/erlang/otp/archive/OTP-17.5.tar.gz'),
            ('17.5.1', 'https://github.com/erlang/otp/archive/OTP-17.5.1.tar.gz'),
            ('17.5.2', 'https://github.com/erlang/otp/archive/OTP-17.5.2.tar.gz'),
        ],

        'elixir': [
            ('1.0.0', 'https://github.com/elixir-lang/elixir/archive/v1.0.0.tar.gz'),
            ('1.0.1', 'https://github.com/elixir-lang/elixir/archive/v1.0.1.tar.gz'),
            ('1.0.2', 'https://github.com/elixir-lang/elixir/archive/v1.0.2.tar.gz'),
            ('1.0.3', 'https://github.com/elixir-lang/elixir/archive/v1.0.3.tar.gz'),
            ('1.0.4', 'https://github.com/elixir-lang/elixir/archive/v1.0.4.tar.gz'),
        ]
    }

    LATEST = 'latest'

    HOME = os.path.join(os.path.expanduser('~'), '.nectar')

    def __init__(self):
        self.make_nectar_dir()
        self.dnlds = os.path.join(self.HOME, 'downloads')
        self.build = os.path.join(self.HOME, 'build')
        self.bin = os.path.join(self.HOME, 'bin')
        self.otpver, self.exver = self.read_version_file()

    def set_executable_links(self, otpver, exver):
        with self.change_directory(self.bin):
            self.symlink_executables(os.path.join(self.build, otpver, 'local', 'bin'))
            self.symlink_executables(os.path.join(self.build, otpver, exver, 'local', 'bin'))
        self.write_version_file(otpver, exver)

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

    def download_erlang(self, version=LATEST):
        outfile, url = self.interpret_version('erlang', version)
        if os.path.isfile(outfile):
            return outfile
        tarfile = self.download(outfile, url)
        return tarfile

    def build_erlang(self, version, jobs):
        if version == self.LATEST:
            version = self.VERSIONS['erlang'][-1][0]
        tarfile = os.path.join(self.dnlds, 'otp-OTP-' + version + '.tar')
        outdir = os.path.join(self.build, version)
        try:
            os.mkdir(outdir)
            os.mkdir(os.path.join(outdir, 'local'))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        # return if Erlang has already been installed
        if glob.glob(os.path.join(outdir, 'local', '*')):
            return

        subprocess.check_call(['tar', 'xzvf', tarfile, '--directory', outdir])
        build_dir = os.path.join(outdir, 'otp-OTP-' + version)
        prefix_path = os.path.join(outdir, 'local')
        with self.change_directory(build_dir):
            os.environ['ERL_TOP'] = build_dir
            subprocess.check_call(['./otp_build', 'autoconf'])
            subprocess.check_call(['./configure', '--prefix=%s' % prefix_path])
            subprocess.check_call(['gmake', '-j%d' % jobs])
            subprocess.check_call(['gmake', 'install'])

    ## ELIXIR METHODS

    def download_elixir(self, version=LATEST):
        outfile, url = self.interpret_version('elixir', version)
        if os.path.isfile(outfile):
            return outfile
        tarfile = self.download(outfile, url)
        return tarfile

    def build_elixir(self, version, otp_version, jobs):
        if version == self.LATEST:
            version = self.VERSIONS['elixir'][-1][0]
        if otp_version == self.LATEST:
            otp_version = self.VERSIONS['erlang'][-1][0]

        self.ensure_erlang(otp_version, jobs)
        tarfile = os.path.join(self.dnlds, 'elixir-' + version + '.tar')
        outdir = os.path.join(self.build, otp_version, version)
        try:
            os.mkdir(outdir)
            os.mkdir(os.path.join(outdir, 'local'))
            os.mkdir(os.path.join(outdir, 'local', 'bin'))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        # return if Elixir has already been installed
        if glob.glob(os.path.join(outdir, 'local', 'bin', '*')):
            return

        subprocess.check_call(['tar', 'xzvf', tarfile, '--directory', outdir])
        build_dir = os.path.join(outdir, 'elixir-' + version)
        otp_path = os.path.join(self.build, otp_version, 'local', 'bin')
        with self.change_directory(build_dir):
            os.environ['PATH'] = otp_path + ':' + os.environ['PATH']
            subprocess.check_call(['gmake', '-j%d' % jobs])

        with self.change_directory(os.path.join(outdir, 'local', 'bin')):
            for tool in ('elixir', 'elixirc', 'iex', 'mix'):
                os.symlink(os.path.join(build_dir, 'bin', tool), tool)

    ## PRIVATE

    def symlink_executables(self, directory):
        for exe in glob.glob(os.path.join(directory, '*')):
            name = os.path.basename(exe)
            if os.path.islink(name):
                os.remove(name)
            os.symlink(exe, name)

    def make_nectar_dir(self):
        try:
            os.mkdir(self.HOME)
            os.mkdir(os.path.join(self.HOME, 'downloads'))
            os.mkdir(os.path.join(self.HOME, 'build'))
            os.mkdir(os.path.join(self.HOME, 'bin'))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    def read_version_file(self):
        version_file = os.path.join(self.HOME, 'version.json')
        try:
            with open(version_file, 'r') as f:
                result = json.load(f)
            return result['erlang'], result['elixir']

        except IOError:
            return None, None

    def write_version_file(self, erlang, elixir):
        version_file = os.path.join(self.HOME, 'version.json')
        with open(version_file, 'w') as f:
            json.dump({'erlang': erlang, 'elixir': elixir}, f)

    def interpret_version(self, tool, version):
        if version == self.LATEST:
            res = [self.VERSIONS[tool][-1]]
        else:
            res = list(filter(lambda x: x[0] == version, self.VERSIONS[tool]))
            if not res:
                raise BadVersion('%s %s is not valid' % (tool, version))

        version, url = res[0]
        if tool == 'erlang':
            tarfile = 'otp-OTP-' + version + '.tar'
        else:
            tarfile = 'elixir-' + version + '.tar'
        return os.path.join(self.dnlds, tarfile), url

    def download(self, outfile, url):
        response = urllib2.urlopen(url, cafile='/usr/local/share/certs/ca-root-nss.crt')
        with open(outfile, 'w') as f:
            f.write(response.read())
        return outfile

    @contextlib.contextmanager
    def change_directory(self, new_dir):
        prev = os.getcwd()
        os.chdir(new_dir)
        try:
            yield
        finally:
            os.chdir(prev)

    def ensure_erlang(self, version, jobs):
        self.download_erlang(version)
        self.build_erlang(version, jobs)

def options():
    usage = '%(prog)s [help | list | install | use] <arguments>'
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('--otp-version', default='latest', help='Erlang version')
    parser.add_argument('--elixir-version', default='latest', help='Elixir version')
    parser.add_argument('--jobs', default=multiprocessing.cpu_count(), type=int, help='Number of build jobs to run in parallel')
    return parser

def usage(parser):
    parser.print_help()

def list_versions():
    Nectar().list_versions()

def install(otp_version, elixir_version, jobs):
    nectar = Nectar()
    nectar.download_erlang(otp_version)
    nectar.download_elixir(elixir_version)
    nectar.build_elixir(elixir_version, otp_version, jobs)

def use(otp_version, elixir_version):
    nectar = Nectar()
    nectar.set_executable_links(otp_version, elixir_version)

def main(command, argv):
    parser = options()
    args = parser.parse_args(argv[1:])

    if command == 'help':
        usage(parser)
    elif command == 'list':
        list_versions()
    elif command == 'install':
        install(args.otp_version, args.elixir_version, args.jobs)
    elif command == 'use':
        use(args.otp_version, args.elixir_version)
    else:
        print('%s: error: unknown command', sys.argv[0])
        usage()
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    import multiprocessing
    import sys

    if len(sys.argv) < 2:
        print('%s: error: must use one of the following commands' % sys.argv[0])
        print('    help\n'
              '    list\n'
              '    install\n'
              '    use')
        sys.exit(1)

    main(sys.argv.pop(1), sys.argv)
