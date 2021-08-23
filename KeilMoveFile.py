import argparse
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    cmdParser = argparse.ArgumentParser(
        description='Move a directory or file used in keil project', prog="KeilMove")
    cmdParser.add_argument('--prj', action='store', dest='keilPrjFile', nargs=1, type=KeilPrjFile,
                           required=True, help='Keil project file')
    cmdParser.add_argument(
        '--move', action='append', dest='toCopy', nargs=1, required=False, type=SrcDstPath, help='Folder to move')
    cmdParser.add_argument(
        '-v', '--verbose', action='store_true', dest='verbosity', help="increase output verbosity")
    cmdParser.add_argument(
        '--no_move', action='store_true', dest='no_move', help="don't preform the actual move just fix the project file")
    args = cmdParser.parse_args()
    keilPrjFile = args.keilPrjFile[0]
    toCopy = args.toCopy[0]

    global verboseprint
    verboseprint = print if args.verbosity else lambda *a, **k: None

    for objToCopy in toCopy:
        if not args.no_move:
            normalMove(objToCopy)
        keilPrjFile.move_dir(objToCopy)


class SrcDstPath:
    def __init__(self, str):
        self.strPassed = str.split(",", 1)
        assert len(self.strPassed) == 2, 'pass 2 paths (\{src\}, \{dst\})'
        self.src = Path(self.strPassed[0]).absolute()
        self.dst = Path(self.strPassed[1]).absolute()
        assert len(self.strPassed) == 2
        assert self.src.is_file() or self.src.is_dir(
        ), "src [{}] doesn't exist".format(self.src)

    def __str__(self):
        return 'dest ' + str(self.src) + ' src ' + str(self.dst)


class KeilPrjFile:
    FILE_EXT = '.uvprojx'

    def __init__(self, filename):
        self.path = Path(filename)
        assert self.path.is_file(), '{} is not a path to a file'.format(self.path)
        assert os.path.splitext(self.path)[
            1] == KeilPrjFile.FILE_EXT, '{} is not a keil prj file'.format(self.path)
        self.xmlTree = ET.parse(filename)
        self.xmlroot = self.xmlTree.getroot()

    def save_file(self, path=None):
        if path == None:
            path = self.path

        self.xmlTree.write(self.path, xml_declaration=True,
                           encoding="utf-8", short_empty_elements=False)

    def move_dir(self, srcDstPath):
        commonPath = os.path.commonpath([srcDstPath.src, srcDstPath.dst])
        srcStrToReplace = str(os.path.relpath(srcDstPath.src, commonPath))
        dstStrToReplace = str(os.path.relpath(srcDstPath.dst, commonPath))
        verboseprint(srcStrToReplace +
                     ' will be replaced with ' + dstStrToReplace)

        verboseprint("Fixing files Paths")
        for file_path_iter in self.xmlroot.iter('FilePath'):
            if file_path_iter.text != None:
                file_path_iter.text = fix_path(
                    file_path_iter.text, srcStrToReplace, dstStrToReplace)

        verboseprint("Fixing include paths")
        for include_paths_iter in self.xmlroot.iter('IncludePath'):
            if include_paths_iter.text != None:
                include_paths = str.split(include_paths_iter.text, ';')

                for count, include_path in enumerate(include_paths):
                    include_paths[count] = fix_path(include_path,
                                                    srcStrToReplace, dstStrToReplace)

                include_paths_iter.text = ';'.join(include_paths)
        self.save_file()


def fix_path(path, str_to_replace, str_to_replace_with):
    new_path = path.replace(
        str_to_replace, str_to_replace_with, 1)
    if new_path != path:
        verboseprint("replaced " + path + " with " + new_path)
        return new_path
    return path


def gitMove(srcDstPath):
    verboseprint("Move " + str(srcDstPath))
    os.system('git mv {} {}'.format(srcDstPath.src, srcDstPath.dst))


def normalMove(srcDstPath):
    verboseprint("Moved " + str(srcDstPath))
    shutil.move(srcDstPath.src, srcDstPath.dst)


if __name__ == '__main__':
    main()
