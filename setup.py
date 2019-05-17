from setuptools import setup, find_packages

setup(
    name = 'agent-concept',
    version = '0.1.0',
    auther = 'Daniel Bluhm',
    author_email = 'daniel.bluhm@sovrin.org',
    description = 'Exploration into a different way of setting up agents.',
    license = 'Apache 2.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
)
