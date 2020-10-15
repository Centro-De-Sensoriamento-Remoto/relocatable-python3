make:
	pip3 install zc.buildout distro
	buildout bootstrap
	bin/buildout
	bin/build

pack:
	bin/pack
