from setuptools import setup, find_packages

setup(
    name='btw_schemes',
    version='0.0.1',
    description='Discord app to manage event attendees',
    author='John Major',
    author_email='john@daylilyinformatics.com',
    url='https://github.com/iamh2o/btw_schemes',
    packages=find_packages(),
    install_requires=[
        'yaml_config_day',
        'requests',
        'pytz',
        'discord.py',
    ]
)
