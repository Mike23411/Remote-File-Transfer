from pathlib import Path
import sys
import colorama
import os
import console

colorama.init()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0;0m'


class myPath:
    def __init__(self, initial_path):
        self.path = Path(initial_path)

    def __str__(self):
        return self.path.__str__()

    def ls(self, print_ls=False):
        all_files = [x for x in self.path.iterdir()]
        dirs = [x for x in all_files if x.is_dir()]
        files = [x for x in all_files if x.is_file()]

        if print_ls:
            print(bcolors.OKBLUE + '.')
            print(bcolors.OKBLUE + '..')
            for i in dirs:
                print(bcolors.OKBLUE + i.name)
            for i in files:
                print(bcolors.RESET + i.name)
        print(bcolors.RESET, end='')
        return all_files

    def cd_mult(self, path):
        orig_path = self.path

        abs_path = Path(path)
        if abs_path.is_absolute():
            self.path = Path(abs_path.parts[0])
            path = ''.join(abs_path.parts[1:])
            if path == '':
                return True
        dirs = path.split('/')
        for d in dirs:
            if not self.cd(d):
                self.path = orig_path
                print('Path change failed: ', end='')
                print(path)
                return False
        self.path = self.path.resolve()
        return True

    def cd(self, dir):
        if dir == '..' or dir == '.':
            self.path = self.path / dir
            return True
        dirs = [x for x in self.ls() if x.is_dir()]
        for d in dirs:
            if dir == d.name:
                self.path = self.path / dir
                return True
        print('cd FAILED')
        return False


def print_ls(ls_tuple):
    print(bcolors.OKBLUE + '.')
    print(bcolors.OKBLUE + '..')
    for x in ls_tuple:
        if x[1]:
            print(bcolors.OKBLUE + x[0])

    for x in ls_tuple:
        if not x[1]:
            print(bcolors.RESET + x[0])
