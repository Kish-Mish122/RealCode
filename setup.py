from setuptools import setup

setup(
    name="real-code",
    version="1.0.0",
    py_modules=["main"], # Явно заставляем упаковать ваш main.py
    entry_points={
        "console_scripts": [
            "real-code-bin=main:main", # Создает исполняемую команду
        ],
    },
)

