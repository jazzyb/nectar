from setuptools import setup

setup(name='nectar',
      version='0.2.0',
      description='Yet another Elixir/OTP version manager',
      url='https://github.com/jazzyb/nectar',
      author='Jason M Barnes',
      author_email='json.barnes@gmail.com',
      license='MIT',
      requires=['six'],
      packages=['nectar'],
      scripts=['nec']
)
