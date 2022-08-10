from setuptools import setup, find_packages

VERSION = "2.4.0"

install_requires = [
    "JSON-log-formatter>=0.2.0",
    "ddtrace>=1.3.2",  # Let's leap ahead 
    "typer>=0.3.0"
]

setup(
    name="muselog",
    version=VERSION,
    description="themuse.com log utilities",
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=install_requires,
    extras_require={
        "django": ["Django>=2.2.12"],
        "flask": ["Flask>=2.1.3"],
        "tornado": ["tornado>=4.5.1"],
        "asgi": ["starlette>=0.13.6"]
    },
    entry_points={
        "console_scripts": [
            "muselog-run = muselog.commands.muselog_run:app",
        ],
    },
)
