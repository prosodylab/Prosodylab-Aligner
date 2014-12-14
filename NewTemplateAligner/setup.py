from setuptools import setup


setup(name="Prosodylab-Aligner",
      version="2.0",
      description="Forced alignment with HTK",
      author="Kyle Gorman",
      author_email="gormanky@ohsu.edu",
      url="http://github.com/kylebgorman/Prosodylab-Aligner/",
      install_requires=["PyYAML >= 3.11",
                        "scipy >= 0.14.0"],
      packages=["aligner"])
