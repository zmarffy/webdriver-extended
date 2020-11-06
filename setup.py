import re
from os.path import join as join_path

import setuptools

with open(join_path("webdriver_extended", "__init__.py"), encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setuptools.setup(
    name='webdriver-extended',
    version=version,
    author='Zeke Marffy',
    author_email='zmarffy@yahoo.com',
    packages=setuptools.find_packages(),
    url='https://github.com/zmarffy/webdriver-extended',
    license='MIT',
    description='webdriver with more features',
    python_requires='>=3.6',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        "selenium",
        "zmtools>=1.1.0"
    ],
)
