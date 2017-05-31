#!/usr/bin/env python

import subprocess
import os
import shutil
import tempfile
import re
import glob

OSV_DIR = '/git-repos/osv'
RECIPES_DIR = '/recipes'
RESULTS_DIR = '/result'

# final osv-loader location e.g. /results/osv-loader.qemu
result_osv_loader_file = os.path.join(RESULTS_DIR, 'osv-loader.qemu')
# final osv-loader index location e.g. /results/index.yaml
result_osv_loader_index_file = os.path.join(RESULTS_DIR, 'index.yaml')


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _print_ok(txt):
    print(Colors.OKGREEN + Colors.BOLD + txt + Colors.ENDC)


def _print_err(txt):
    print(Colors.FAIL + Colors.BOLD + txt + Colors.ENDC)


def _print_warn(txt):
    print(Colors.WARNING + 'WARN: ' + txt + Colors.ENDC)


class Recipe:
    def __init__(self, root, name):
        # package name e.g. eu.mikelangelo-project.osv.bootstrap
        self.name = name
        # where recipe is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap
        self.dir = os.path.join(root, name)

        # where recipe demo is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo
        self.demo_dir = os.path.join(self.dir, 'demo')
        # where recipe demo package is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo/package
        self.demo_pkg_dir = os.path.join(self.demo_dir, 'pkg')
        # where recipe demo expected stdout is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo/expected-stdout.txt
        self.demo_expect = os.path.join(self.demo_dir, 'expected-stdout.txt')
        # where recipe demo package.yaml template is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo/package/meta/package.yaml.templ
        self.demo_yaml_templ = os.path.join(self.demo_pkg_dir, 'meta', 'package.yaml.templ')
        # where recipe demo package.yaml is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo/package/meta/package.yaml
        self.demo_yaml = os.path.join(self.demo_pkg_dir, 'meta', 'package.yaml')
        # where recipe demo run.yaml is e.g. /recipes/eu.mikelangelo-project.osv.bootstrap/demo/package/meta/run.yaml
        self.demo_run_yaml = os.path.join(self.demo_pkg_dir, 'meta', 'run.yaml')

        # where recipe results are e.g. /results/eu.mikelangelo-project.osv.bootstrap
        self.result_dir = os.path.join(RESULTS_DIR, self.name)
        # final .mpm location e.g. /results/eu.mikelangelo-project.osv.bootstrap.mpm
        self.result_mpm_file = os.path.join(RESULTS_DIR, '%s.mpm' % self.name)
        # final .yaml location e.g. /results/eu.mikelangelo-project.osv.bootstrap.yaml
        self.result_yaml_file = os.path.join(RESULTS_DIR, '%s.yaml' % self.name)
        # intermediate .mpm location e.g. /results/eu.mikelangelo-project.osv.bootstrap/eu.mikelangelo-project.osv.bootstrap.mpm
        self.result_orig_mpm_file = os.path.join(self.result_dir, '%s.mpm' % self.name)
        # intermediate .yaml location e.g. /results/eu.mikelangelo-project.osv.bootstrap/meta/package.yaml
        self.result_orig_yaml_file = os.path.join(self.result_dir, 'meta', 'package.yaml')

        # where osv source code is e.g. /git-repos/osv
        self.osv_dir = OSV_DIR

        # should be this recipe built using clone of osv dir (set to False for debugging to speed things up)
        self.do_isolate_osv_dir = False
        # does this recipe contain demo package
        self.has_demo_package = os.path.isfile(self.demo_run_yaml)


def prepare_osv_scripts():
    """
    prepare_osv_scripts() prepares whatever is needed when container is first run after being built. Namely,
    it applies patches to selected OSv scripts.      
    """
    _print_ok('Prepare OSv scripts')

    with open('/common/skip_vm_uploads.patch', 'r') as f:
        c = 'patch -p1'
        p = subprocess.Popen(
            c.split(),
            cwd=OSV_DIR,
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = p.communicate()

        if p.returncode != 0:
            _print_err('Applying patch /common/skip_vm_uploads.patch returned non-zero status code')
            print('--- STDOUT: ---\n%s' % output)
            print('--- STDERR: ---\n%s' % error)

    with open('/common/upload_manifest.py.patch', 'r') as f:
        c = 'patch -p1'
        p = subprocess.Popen(
            c.split(),
            cwd=OSV_DIR,
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = p.communicate()

        if p.returncode != 0:
            _print_err('Applying patch /common/upload_manifest.py.patch returned non-zero status code')
            print('--- STDOUT: ---\n%s' % output)
            print('--- STDERR: ---\n%s' % error)


def clear_result_dir():
    """
    clear_result_dir() deletes whatever is currently in RESULTS_DIR.
    """
    _print_ok('Clearing result directory %s' % RESULTS_DIR)

    for name in os.listdir(RESULTS_DIR):
        path = os.path.join(RESULTS_DIR, name)
        if os.path.isfile(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)


def provide_loader_image():
    """
    provide_mike_osv_loader() copies loader image from OSv build directory into /result directory.
    """
    _print_ok('Providing loader image into result directory %s' % RESULTS_DIR)

    print('Copy loader.img')
    shutil.copy2(os.path.join(OSV_DIR, 'build', 'last', 'loader.img'), result_osv_loader_file)

    print('Create index.yaml')
    s = '''
        format_version: "1"
        version: "v0.24-116-g73b38d8"
        created: "2016-06-11T15:41:07"
        description: "OSv Bootloader"
        build: "scripts/build"
    '''

    with open(result_osv_loader_index_file, 'w') as f:
        f.write(s)

    print('Set permissions to 0777')
    os.chmod(result_osv_loader_file, 0777)
    os.chmod(result_osv_loader_index_file, 0777)


def list_recipes(root):
    """
    list_recipes() searches for folders in given direcotry and instantiates Recipe object for each. 
    :param root: directory where recipes folders are in
    :return: list of Recipe instances
    """
    return [Recipe(root, name) for name in os.listdir(root) if os.path.isdir(os.path.join(root, name))]


def build_recipe(recipe):
    """
    build_recipe() runs recipe's "build.sh" script within the prepared context. Result of build.sh script is
    uncompressed Capstan package folder RESULT_DIR/{recipe.name} that contains at least meta/package.yaml file.
    
    :param recipe: Recipe instance
    :return: True if build was successful, False otherwise
    """
    _print_ok('Building recipe %s' % recipe.name)

    if recipe.do_isolate_osv_dir:
        print('Preparing isolated osv folder')
        osv_dir_clone = os.path.join(tempfile.mkdtemp(), 'osv')
        shutil.copytree(recipe.osv_dir, osv_dir_clone, symlinks=True)
        recipe.osv_dir = osv_dir_clone

    print('Preparing result directory for recipe')
    shutil.rmtree(recipe.result_dir, ignore_errors=True)
    os.makedirs(recipe.result_dir)

    print('Running build.sh script')
    p = subprocess.Popen(
        './build.sh',
        cwd=recipe.dir,
        env={
            'RECIPE_DIR': recipe.dir,
            'PACKAGE_RESULT_DIR': recipe.result_dir,
            'PACKAGE_NAME': recipe.name,

            'OSV_DIR': recipe.osv_dir,
            'OSV_BUILD_DIR': os.path.join(recipe.osv_dir, 'build', 'release.x64'),
            'GCCBASE': os.path.join(recipe.osv_dir, 'external', 'x64', 'gcc.bin'),
            'MISCBASE': os.path.join(recipe.osv_dir, 'external', 'x64', 'misc.bin'),
            'PATH': os.environ.get('PATH'),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()

    if p.returncode != 0:
        _print_err('build.sh returned non-zero status code for recipe %s:' % recipe.dir)
        print('--- STDOUT: ---\n%s' % output)
        print('--- STDERR: ---\n%s' % error)
        return False

    print('Verifying that result contains meta/package.yaml')
    if not os.path.isfile(recipe.result_orig_yaml_file):
        _print_err('build.sh script did not create meta/package.yaml file')
        return False

    print('Set permissions to 0777')
    os.chmod(recipe.result_dir, 0777)

    if recipe.do_isolate_osv_dir:
        print('Cleanup')
        shutil.rmtree(recipe.osv_dir, ignore_errors=True)

    return True


def provide_mpm_for_recipe(recipe):
    """
    provide_mpm_for_recipe() compresses result of build_recipe() into .mpm file and provides it into /result directory.
    This function should only be called after build_recipe() succeeded.
    :param recipe: Recipe instance
    :return: True on success, False otherwise
    """
    _print_ok('Providing mpm for package "%s" into result directory %s' % (recipe.name, RESULTS_DIR))

    print('capstan package build')
    p = subprocess.Popen(
        'capstan package build'.split(),
        cwd=recipe.result_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()

    if p.returncode != 0:
        _print_err('"capstan package build" returned non-zero status code for package %s:' % recipe.result_dir)
        print('--- STDOUT: ---\n%s' % output)
        print('--- STDERR: ---\n%s' % error)
        return False

    print('Copy .mpm and .yaml')
    if os.path.exists(recipe.result_mpm_file):
        os.remove(recipe.result_mpm_file)
    shutil.move(recipe.result_orig_mpm_file, recipe.result_mpm_file)
    shutil.copy2(recipe.result_orig_yaml_file, recipe.result_yaml_file)

    print('Set permissions to 0777')
    os.chmod(recipe.result_mpm_file, 0777)
    os.chmod(recipe.result_yaml_file, 0777)

    return True


def prepare_test_capstan_root():
    """
    prepare_test_capstan_root() creates a fresh temporary CAPSTAN_ROOT with all the newly compiled packages in it.
    :return: path to CAPSTAN_ROOT
    """
    print('Generating fresh CAPSTAN_ROOT')
    capstan_root = tempfile.mkdtemp()
    print('CAPSTAN_ROOT=%s' % capstan_root)

    print('Copying all mpms and yamls into CAPSTAN_ROOT')
    repo_packages_dir = os.path.join(capstan_root, 'packages')
    os.mkdir(repo_packages_dir)
    mpms = list(glob.iglob(os.path.join(RESULTS_DIR, "*.mpm")))
    yamls = list(glob.iglob(os.path.join(RESULTS_DIR, "*.yaml")))
    for file in mpms + yamls:
        shutil.copy2(file, repo_packages_dir)
    print('Number of mpms copied: %d' % len(mpms))

    print('Copying mike/osv-loader into CAPSTAN_ROOT')
    repo_osv_loader_dir = os.path.join(capstan_root, 'repository', 'mike', 'osv-loader')
    os.makedirs(repo_osv_loader_dir)
    shutil.copy2(result_osv_loader_file, repo_osv_loader_dir)
    shutil.copy2(result_osv_loader_index_file, repo_osv_loader_dir)

    return capstan_root


def test_recipe(recipe):
    """
    test_recipe() composes and runs demo for given recipe and verifies that unikernel printed expected text to console.
    :param recipe: Recipe instance
    :return: True if test was successfule, False if not
    """
    _print_ok('Testing recipe %s' % recipe.name)

    capstan_root = prepare_test_capstan_root()

    print('Generating package.yaml based on package.yaml.templ template.')
    content = ''
    with open(recipe.demo_yaml_templ, 'r') as f:
        content = f.read()
    content = content.replace('${PACKAGE_NAME}', recipe.name)
    with open(recipe.demo_yaml, 'w') as f:
        f.write(content)

    print('capstan package compose demo (demo_pkg_dir=%s)' % recipe.demo_pkg_dir)
    p = subprocess.Popen(
        'capstan package compose demo'.split(),
        cwd=recipe.demo_pkg_dir,
        env={
            'CAPSTAN_ROOT': capstan_root,
            'PATH': os.environ.get('PATH'),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()

    if p.returncode != 0:
        _print_err('"capstan package compose" returned non-zero status code for package %s:' % recipe.demo_pkg_dir)
        print('--- STDOUT: ---\n%s' % output)
        print('--- STDERR: ---\n%s' % error)
        return False

    print('capstan run demo')
    p = subprocess.Popen(
        'capstan run demo'.split(),
        cwd=recipe.demo_pkg_dir,
        env={
            'CAPSTAN_ROOT': capstan_root,
            'PATH': os.environ.get('PATH'),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = p.communicate()

    if p.returncode != 0:
        _print_err('"capstan run" returned non-zero status code for package %s:' % recipe.demo_pkg_dir)
        print('--- STDOUT: ---\n%s' % output)
        print('--- STDERR: ---\n%s' % error)
        return False

    print('Checking if unikernel stdout is as expected')
    expected = ''
    with open(recipe.demo_expect, 'r') as f:
        expected = f.read()
    expected = expected.strip()
    expected = re.sub('\s+', '\\s+', expected).strip()
    expected = expected.replace('(', '\(').replace(')', '\)')
    is_ok = re.search(expected, output) is not None

    if not is_ok:
        _print_err('Unikernel stdout is not as expected')
        print('expected =\n%s' % expected)
        print('obtained =\n%s' % output)
        return False

    print('Cleanup')
    shutil.rmtree(capstan_root, ignore_errors=True)

    return True


if __name__ == '__main__':
    prepare_osv_scripts()
    clear_result_dir()
    provide_loader_image()

    _print_ok('List recipes')
    recipes = list_recipes(RECIPES_DIR)
    print('Recipes are: %s' % [r.name for r in recipes])

    _print_ok('Build listed recipes')
    for recipe in recipes:
        build_ok = build_recipe(recipe)

        if build_ok:
            provide_mpm_for_recipe(recipe)

    _print_ok('Test listed recipes')
    for recipe in recipes:
        if recipe.has_demo_package:
            if test_recipe(recipe):
                print('Test for %s passed.' % recipe.name)
            else:
                _print_err('Test for %s failed.' % recipe.name)
        else:
            _print_warn('Recipe %s contains no demo package' % recipe.name)
