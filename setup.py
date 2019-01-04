from setuptools import setup

VERSION = "1.4.1"

install_requires = [
    "pygelf>=0.4.1",
    "JSON-log-formatter==0.1.0"
]

setup(
    name="muselog",
    version=VERSION,
    description="themuse.com log utilities",
    zip_safe=False,

    packages=["muselog"],

    install_requires=install_requires
)
