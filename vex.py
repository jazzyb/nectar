#!/usr/bin/env python

from __future__ import print_function

import contextlib
import errno
import json
import multiprocessing
import os
import subprocess
import urllib2

class Vex (object):
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

    HOME = os.path.join(os.path.expanduser('~'), '.vex')

    def __init__(self):
        self.make_vexdir()
        self.dnlds = os.path.join(self.HOME, 'downloads')
        self.build = os.path.join(self.HOME, 'build')
        self.local = os.path.join(self.HOME, 'local')
        self.otpver, self.exver = self.read_version_file()

    ## ERLANG METHODS

    def download_erlang(self, version=LATEST):
        outfile, url = self.interpret_version('erlang', version)
        tarfile = self.download(outfile, url)
        return tarfile

    def build_erlang(self, version, jfactor):
        tarfile = os.path.join(self.dnlds, 'otp-OTP-' + version + '.tar')
        outdir = os.path.join(self.build, version)
        try:
            os.mkdir(outdir)
            os.mkdir(os.path.join(outdir, 'local'))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
        subprocess.check_call(['tar', 'xzvf', tarfile, '--directory', outdir])

        build_dir = os.path.join(outdir, 'otp-OTP-' + version)
        prefix_path = os.path.join(outdir, 'local')
        with self.change_directory(build_dir):
            os.environ['ERL_TOP'] = build_dir
            subprocess.check_call(['./otp_build', 'autoconf'])
            subprocess.check_call(['./configure', '--prefix=%s' % prefix_path])
            subprocess.check_call(['gmake', '-j%d' % jfactor])
            subprocess.check_call(['gmake', 'install'])

    ## ELIXIR METHODS

    def download_elixir(self, version=LATEST):
        outfile, url = self.interpret_version('elixir', version)
        tarfile = self.download(outfile, url)
        return tarfile

    ## PRIVATE

    def make_vexdir(self):
        try:
            os.mkdir(self.HOME)
            os.mkdir(os.path.join(self.HOME, 'downloads'))
            os.mkdir(os.path.join(self.HOME, 'build'))
            os.mkdir(os.path.join(self.HOME, 'local'))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    def read_version_file(self):
        version_file = os.path.join(self.HOME, 'version.json')
        try:
            with open(version_file, 'r') as f:
                json = json.load(f)
            return json['erlang'], json['elixir']

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

def main():
    #Vex().download_erlang('17.5.1')
    #Vex().download_elixir(Vex.LATEST)
    Vex().build_erlang('17.5.1')

if __name__ == '__main__':
    main()
