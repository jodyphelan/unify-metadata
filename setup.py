import setuptools

version = [l.strip() for l in open("unify_metadata/__init__.py") if "version" in l][0].split('"')[1]

setuptools.setup(

	name="unify-metadata",

	version=version,
	packages=["unify_metadata"],
	license="GPLv3",
	long_description="Tool of standardising metadata",
	scripts= [
		'scripts/unify-metadata',
		]
)
