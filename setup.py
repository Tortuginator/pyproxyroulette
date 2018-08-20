import io
import re
from collections import OrderedDict

from setuptools import setup

with io.open('pyproxyroulette/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='pyproxyroulette',
    version=version,
    project_urls=OrderedDict((
        ('Documentation', 'https://github.com/Tortuginator/pyproxyroulette'),
        ('Code', 'https://github.com/Tortuginator/pyproxyroulette'),
        ('Issue tracker', 'https://github.com/Tortuginator/pyproxyroulette/issues'),
    )),
    author='Tortuginator',
    description='A simple wrapper for Requests to randomly select proxies',
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages=['pyproxyroulette'],
    install_requires=[
        'Requests>=2.18'
    ],
)