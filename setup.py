from setuptools import setup

VERSION = "1.5.2"

install_requires = [
    "pygelf>=0.4.1",
    "JSON-log-formatter==0.2.0",
    "ddtrace==0.12"
]

setup(
    name="muselog",
    version=VERSION,
    description="themuse.com log utilities",
    zip_safe=False,

    packages=["muselog"],

    install_requires=install_requires
)
