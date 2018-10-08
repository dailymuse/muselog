from setuptools import setup

VERSION = "1.2.1"

install_requires = [
    "pygelf>=0.4.1",
    "python-json-logger==0.1.9"
]

setup(
    name="muselog",
    version=VERSION,
    description="themuse.com log utilities",
    zip_safe=False,

    packages=["muselog"],

    install_requires=install_requires
)
