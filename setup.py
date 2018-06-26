import setuptools
import instagram_scraper

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=instagram_scraper.__name__,
    version=instagram_scraper.__version__,
    author=instagram_scraper.__author__,
    author_email="meetmangukiya98@gmail.com",
    description="Scrape the Instagram frontend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/meetmangukiya/instagram-scraper",
    packages=setuptools.find_packages(),
    install_requires=['requests-html'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    entry_points={
        'console_scripts': [
            'scrape-insta = instagram_scraper.instagram_scraper:run',
        ],
    }
)
