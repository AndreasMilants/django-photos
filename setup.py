from setuptools import setup, find_packages

setup(packages=find_packages(),
      install_requires=[
          "Django >= 2.0",
          "Pillow",
      ],
      )
