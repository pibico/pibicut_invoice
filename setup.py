from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in pibicut_invoice/__init__.py
from pibicut_invoice import __version__ as version

setup(
	name="pibicut_invoice",
	version=version,
	description="TLV QRCode for E-Invoices",
	author="PibiCo",
	author_email="pibico.sl@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
