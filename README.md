# Nectar
========

(Yet another?) Version manager for Erlang/OTP and Elixir.

This script builds and installs OTP and Elixir from Github sources at various
combinations of versions.  It solves the following problem:  **How do I test an
application using different versions of OTP and/or Elixir efficiently?**

I use this script regularly with both Python 2 and 3 on Ubuntu 14.04 and
FreeBSD 10.


### Example Usage
============

See `nec help` for full usage.

```
# install Elixir 1.2.1 with OTP 18.2.2:
$ nec install -o 18.2.2 -x 1.2.1
Downloading erlang 18.2.2...
Downloading elixir 1.2.1...
Extracting erlang 18.2.2...
Building erlang 18.2.2 -- this may take some time...
Extracting elixir 1.2.1...
Building elixir 1.2.1 -- this may take some time...
$

# set the installed version as the default:
$ nec use -o 18.2.2 -x 1.2.1
$ iex --version
Erlang/OTP 18 [erts-7.2.1] [source] [64-bit] [smp:8:8] [async-threads:10] [hipe] [kernel-poll:false]

IEx 1.2.1

# install and use an older version of Elixir:
$ nec install -o 17.5 -x 1.0.5
$ nec use -o 17.5 -x 1.0.5
$ iex --version
Erlang/OTP 17 [erts-6.4] [source] [64-bit] [smp:8:8] [async-threads:10] [hipe] [kernel-poll:false]

Elixir 1.0.5

# view installed versions:
$ nec list
        ERLANG  |       ELIXIR
        ------  |       ------
*       17.5    |       1.0.5
        18.2.2  |       1.2.1

# switch back to newer version:
$ nec use -o 18.2.2 -x 1.2.1
$ iex --version
Erlang/OTP 18 [erts-7.2.1] [source] [64-bit] [smp:8:8] [async-threads:10] [hipe] [kernel-poll:false]

IEx 1.2.1

# remove older version:
$ nec rm -o 17.5 -x 1.0.5
$ nec list
        ERLANG  |       ELIXIR
        ------  |       ------
*       18.2.2  |       1.2.1
```
