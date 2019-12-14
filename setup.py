import io
import re
from collections import OrderedDict

from setuptools import setup
with open("README.md", "r") as fh:
    long_description = fh.read()
    
with io.open('pyproxyroulette/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='pyproxyroulette-TORTUGINATOR',
    version=version,
    project_urls=OrderedDict((
        ('Documentation', 'https://github.com/Tortuginator/pyproxyroulette'),
        ('Code', 'https://github.com/Tortuginator/pyproxyroulette'),
        ('Issue tracker', 'https://github.com/Tortuginator/pyproxyroulette/issues'),
    )),
    author='Tortuginator',
    description='A simple wrapper for Requests to randomly select proxies',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Tortuginator/pyproxyroulette",
    download_url = 'https://github.com/Tortuginator/pyproxyroulette/archive/v0.4.2.tar.gz',
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages=['pyproxyroulette'],
    install_requires=[
        'Requests>=2.18'
    ],
    keywords = ['PROXY', 'REQUESTS', 'PYPROXY', 'ROULETTE','CRAWLER', 'SCRAPER', 'PROXIFY'],
    classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Topic :: Scientific/Engineering',
    'Topic :: System :: Networking',
    'Topic :: Internet :: WWW/HTTP',
    'Programming Language :: Python :: 3', 
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)