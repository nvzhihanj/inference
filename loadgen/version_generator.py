# Creates version definitions used by the loadgen at compile time.

import datetime
import errno
import hashlib
import os
import sys

from absl import app


def func_def(name, string):
    return "const std::string& Loadgen" + name + "() {\n" + \
        "  static const std::string str = " + string + ";\n" + \
        "  return str;\n" + \
        "}\n\n"


# Fof clients that build the loadgen from the git respository without
# any modifications.
def generate_loadgen_version_definitions_git(file, git_command):
    gitRev = os.popen(git_command + "rev-parse --short=10 HEAD").read()
    gitCommitDate = os.popen(git_command + "log --format=\"%cI\" -n 1").read()
    gitStatus = os.popen(git_command + "status -s -uno").read()
    gitLog = os.popen(
        git_command + "log --pretty=oneline -n 16 --no-decorate").read()
    file.write(func_def("GitRevision", "\"" + gitRev[0:-1] + "\""))
    file.write(func_def("GitCommitDate", "\"" + gitCommitDate[0:-1] + "\""))
    file.write(func_def("GitStatus", "R\"(" + gitStatus[0:-1] + ")\""))
    file.write(func_def("GitLog", "R\"(" + gitLog[0:-1] + ")\""))


# For clients that might not import the loadgen code as the original git
# repository.
def generate_loadgen_verstion_definitions_git_stubs(file):
    na = "\"NA\""
    file.write(func_def("GitRevision", na))
    file.write(func_def("GitCommitDate", na))
    file.write(func_def("GitStatus", na))
    file.write(func_def("GitLog", na))


# Always log the sha1 of the loadgen files, regardless of whether we are
# in the original git repository or not.
def generate_loadgen_version_definitions_sha1(file, loadgen_root):
    sha1s = ""
    loadgen_files = \
        ["/bindings/" + s for s in os.listdir(loadgen_root + "/bindings")] + \
        ["/demos/" + s for s in os.listdir(loadgen_root + "/demos")] + \
        ["/" + s for s in os.listdir(loadgen_root)]
    for fn in sorted(loadgen_files):
        full_fn = loadgen_root + fn
        if not os.path.isfile(full_fn):
            continue
        file_data = open(full_fn,"rb").read()
        sha1s += hashlib.sha1(file_data).hexdigest() + \
                 " " + fn + "\n"

    file.write(func_def("Sha1OfFiles", "R\"(" + sha1s[0:-1] + ")\""))


def generate_loadgen_version_definitions(cc_filename, loadgen_root):
    try:
        os.makedirs(os.path.dirname(cc_filename))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    file = open(cc_filename, "w")
    file.write("// DO NOT EDIT: Autogenerated by version_generator.py.\n\n")
    file.write("#include <string>\n\n")
    file.write("namespace mlperf {\n\n")
    file.write(func_def("Version", "\".5a1\""))

    dateTimeNowLocal = datetime.datetime.now().isoformat()
    dateTimeNowUtc = datetime.datetime.utcnow().isoformat()
    file.write(func_def("BuildDateLocal", "\"" + dateTimeNowLocal + "\""))
    file.write(func_def("BuildDateUtc", "\"" + dateTimeNowUtc + "\""))

    git_dir = "--git-dir=\"" + loadgen_root + "/../.git\" "
    git_work_tree = "--work-tree=\"" + loadgen_root + "/..\" "
    git_command = "git " + git_dir + git_work_tree
    gitStatus = os.popen(git_command + "status")
    gitStatus.read()
    is_git_repo = gitStatus.close() == None
    if is_git_repo:
        generate_loadgen_version_definitions_git(file, git_command)
    else:
        generate_loadgen_verstion_definitions_git_stubs(file)
    generate_loadgen_version_definitions_sha1(file, loadgen_root)

    file.write("}  // namespace mlperf\n");
    file.close()


def main(argv):
    if len(argv) != 3:
        raise app.UsageError('Incorrect command-line arguments.')
    generate_loadgen_version_definitions(argv[1], argv[2])


if __name__ == '__main__':
  app.run(main)