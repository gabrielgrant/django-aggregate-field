from setuptools import setup

setup(
    name='django-aggregate-field',
    version='0.1.4',
    author='Gabriel Grant',
    author_email='g@briel.ca',
    description='Access commonly-used aggregations with a model-field-like interface',
    url='https://github.com/gabrielgrant/django-aggregate-field',
    packages=['aggregate_field',],
    license='LGPL',
    long_description=open('README').read(),
    install_requires=[
        'django',
    ],
)

