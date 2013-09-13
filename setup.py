from os.path import abspath, dirname, join
from setuptools import setup, find_packages

here = abspath(dirname(__file__))
README = '\n'.join([open(join(here, 'README')).read(),
    open(join(here, 'CHANGES')).read()])

requires = []

setup(name='stepford',
    keywords='python,facebook,integration test,test users',
    version='0.1',
    description='An implementation of the Facebook test user API',
    author='Demian Brecht',
    author_email='demianbrecht@gmail.com',
    url='https://github.com/demianbrecht/stepford',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    long_description=README,
    install_requires=requires,
    packages=find_packages(),
    test_suite='tests.TestStepford',
)
