from setuptools import setup

extras_require = {
    "test": [
        "pytest",
        "pytest-cov>=2.5.1",
        "pydocstyle",
        "check-manifest",
        "flake8",
        "black",
    ],
}
extras_require["develop"] = sorted(
    set(extras_require["test"] + ["pre-commit", "twine"])
)
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    extras_require=extras_require,
    use_scm_version=lambda: {"local_scheme": lambda version: ""},
)
