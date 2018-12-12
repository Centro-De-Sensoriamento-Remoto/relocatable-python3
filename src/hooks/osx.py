__import__("pkg_resources").declare_namespace(__name__)

def _catch_and_print(func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except (OSError, IOError) as e:
        print(e)

def find_files(directory, pattern):
    import os
    import fnmatch
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

def change_install_name_in_file(filepath):
    from re import sub
    print("pre-configure-hook: changing install_name in %s" % filepath)
    content = open(filepath).read()
    pattern = r'-install_name .*/(.*) '
    repl = r'-install_name @rpath/\1 '
    open(filepath, 'w').write(sub(pattern, repl, content))

def remove_rpath_in_file(filepath):
    print("pre-configure-hook: removing rpath in %s" % filepath)
    content = open(filepath).read()
    content = content.replace(r'$rpath/$soname', r'@rpath/$soname')
    content = content.replace(r'\$rpath/\$soname', r'@rpath/\$soname')
    content = content.replace(r'\$rpath/\$soname', r'@rpath/\$soname')
    content = content.replace(r'${wl}-rpath ${wl}$libdir', '')
    content = content.replace(r'${wl}-rpath,$libdir', '')
    content = content.replace(r'-rpath $libdir', '')
    open(filepath, 'w').write(content)

def change_install_name(options, buildout, version):
    from os import curdir
    from os.path import abspath
    for item in find_files(abspath(curdir), 'configure'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'Makefile'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'configure.in'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'Makefile.in'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'libtool'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'aclocal.m4'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)
    for item in find_files(abspath(curdir), 'shobj-conf'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)

def patch_ncurses(options, buildout, version):
    from os import curdir
    from os.path import abspath
    for item in find_files(abspath(curdir), 'Makefile'):
        print('fixing files "%s"' % item)
        filepath = item
        content = open(filepath).read()
        content.replace('LIBRARIES\t=  ../lib/libncurses.dylib', 'LIBRARIES\t=  ../lib/libncurses.${ABI_VERSION}.dylib')
        content.replace('-o$@', '-o $@')
        open(filepath, 'w').write(content)

def symlink_ncurses(options, buildout, version):
    from os import symlink
    from os.path import join, exists
    dist = options["prefix"]
    dist_lib = join(dist, "lib")
    files = [('libncurses++w.a', 'libncurses++.a'),
             ('libncurses.a', 'libcurses.a'),
             ('libncurses.dylib', 'libcurses.dylib'),
             ('libncurses.a', 'libcurses.a'),
             ('libncurses_g.a', 'libcurses_g.a')]
    for src, dst in files:
        if exists(join(dist_lib, src)) and not exists(join(dist_lib, dst)):
            symlink(join(dist_lib, src), join(dist_lib, dst))


def patch_openssl(options, buildout, version):
    from os import curdir
    from os.path import abspath
    for item in find_files(abspath(curdir), 'Makefile*'):
        print('fixing files "%s"' % item)
        filepath = item
        content = open(filepath).read()
        content = content.replace('-Wl,-rpath,$(LIBRPATH)', '')
        content = content.replace('-Wl,-rpath,$(LIBPATH)', '')
        content = content.replace('-rpath $(LIBRPATH)', '')
        content = content.replace("-install_name $(INSTALLTOP)/$(LIBDIR)", "-install_name @rpath")
        open(filepath, 'w').write(content)


def patch_pdb(options, buildout, version):
    import pdb
    pdb.set_trace()

def patch_cyrus_sasl(options, buildout, version):
    change_install_name(options, buildout, version)
    from os import curdir
    from os.path import abspath
    for item in find_files(abspath(curdir), 'ltconfig'):
        change_install_name_in_file(item)
        remove_rpath_in_file(item)

def patch_python(options, buildout, version):
    from os.path import abspath
    change_install_name(options, buildout, version)
    for file in ['Makefile.pre.in', 'configure']:
        content = open(file).read()
        print(abspath('./%s' % file))
        assert len(content)
        content = content.replace(r'-install_name,$(prefix)/lib', '-install_name,@rpath')
        content = content.replace(r'-install_name $(DESTDIR)$(PYTHONFRAMEWORKINSTALLDIR)/Versions/$(VERSION)', '-install_name @rpath')
        content = content.replace(r'-install_name $(PYTHONFRAMEWORKINSTALLDIR)/Versions/$(VERSION)', '-install_name @rpath')
        assert '@rpath' in content
        open(file, 'w').write(content)

def add_ld_library_path_to_python_makefile(options, buildout, version):
    # Inject LD_LIBRARY_PATH to setup.py's runtime (see comment in add_ld_library_path_to_configure)
    # without this, the dynamic modules will fail to load and be renamed to *_failed.so
    from os.path import join
    dist = options["prefix"]
    dist_lib = join(dist, "lib")
    filename = "Makefile"
    content = open(filename).read()
    content = content.replace('$(PYTHON_FOR_BUILD) $(srcdir)/setup.py', 'LD_LIBRARY_PATH={} $(PYTHON_FOR_BUILD) $(srcdir)/setup.py'.format(dist_lib))
    open(filename, 'w').write(content)

def patch_python_Makefile_after_configure(options, buildout, version):
    import re
    filename = "Makefile"
    content = open(filename).read()
    content = re.sub(r"LDFLAGS=", r"LDFLAGS=-Wl,-rpath,@loader_path/../lib ", content)
    open(filename, 'w').write(content)
    add_ld_library_path_to_python_makefile(options, buildout, version)


def patch_libevent_configure_in(options, buildout, version):
    from os import curdir
    from os.path import abspath
    for item in find_files(abspath(curdir), 'configure.in*'):
        print('fixing files "%s"' % item)
        filepath = item
        content = open(filepath).read()
        content = content.replace('AM_CONFIG_HEADER', 'AC_CONFIG_HEADERS')
        open(filepath, 'w').write(content)

def add_ld_library_path_to_configure(options, buildout, version):
    # The LD_LIBRARY_PATH (runtime search path) that is set by buildout is not passed to
    # the childrent processes due to SIP on El Capitan and newer. We set it manually inside the configure script
    from os import curdir
    from os.path import abspath, join
    filepath = join(abspath(curdir), 'configure')
    print('fixing files "%s"' % filepath)
    content = open(filepath).read()
    dist = options["prefix"]
    dist_lib = join(dist, "lib")
    content = "export LD_LIBRARY_PATH={}\n".format(dist_lib) + content
    open(filepath, 'w').write(content)

def autogen(options, buildout, version):
    from subprocess import Popen
    patch_libevent_configure_in(options, buildout, version)
    process = Popen(['./autogen.sh'])
    assert process.wait() == 0
    change_install_name(options, buildout, version)

def autoreconf(options, buildout, version):
    from subprocess import Popen
    patch_libevent_configure_in(options, buildout, version)
    process = Popen(['autoreconf'])
    assert process.wait() == 0
    change_install_name(options, buildout, version)


def post_build_install_name(options, buildout, version):
    import os
    directory = options["prefix"]
    install_name_tool(os.path.join(directory, 'lib'), directory, '@loader_path/../lib/', "*.dylib")
    install_name_tool(os.path.join(directory, 'lib'), directory, '@loader_path/../lib/', "*.so")
    install_name_tool(os.path.join(directory, 'bin'), directory, '@loader_path/../lib/')
    install_name_tool(os.path.join(directory, 'sbin'), directory, '@loader_path/../lib/')


def install_name_tool(walk_path, hardcode_prefix, dynamic_prefix, file_pattern="*"):
    import os
    import subprocess
    import re
    dylib_pattern = re.compile(r'\s*(.*)\s+\(')
    for file_name in find_files(walk_path, file_pattern):
        if os.path.islink(file_name):
            continue

        p = subprocess.Popen(['otool', '-L', file_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, err = p.communicate()
        rc = p.returncode
        output = output.decode()
        libs = dylib_pattern.findall(output)
        for l in libs:
            if hardcode_prefix in l:
                lib = os.path.basename(l)
                subprocess.call(['install_name_tool', '-change', l, dynamic_prefix + lib, file_name])
        subprocess.call(['install_name_tool', '-change', hardcode_prefix + '/lib', dynamic_prefix, file_name])
