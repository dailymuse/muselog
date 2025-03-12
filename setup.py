from setuptools import setup, find_packages

VERSION = "2.8.0"

install_requires = [
    "JSON-log-formatter>=0.2.0",
    "ddtrace @ git+https://github.com/ellingtonjp/dd-trace-py.git@ea12f34c3c3555e244d0e965dee7314b78a27fa1",
    "typer>=0.3.0"
]

setup(
    name="muselog",
    version=VERSION,
    description="themuse.com log utilities",
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "django": ["Django>=2.2.12"],
        "flask": ["Flask>=2.3.3"],
        "tornado": ["tornado>=4.5.1"],
        "asgi": ["starlette>=0.31.1"]
    },
    entry_points={
        "console_scripts": [
            "muselog-run = muselog.commands.muselog_run:app",
        ],
    },
)
