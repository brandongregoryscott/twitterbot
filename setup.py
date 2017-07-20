try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='twitterbot',
    version='0.1.0',
    author='thricedotted',
    author_email='thricedotted@gmail.com',
    packages=['twitterbot'],
    description='A simple Python framework for creating Twitter bots.',
    install_requires=[
        "twython >= 3.1.2"
    ],
)
