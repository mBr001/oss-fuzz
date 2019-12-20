# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module to get the the name of a git repo containing a specific commit
inside of an OSS-Fuzz project.

Example Usage:

  detect_repo.py --src_dir /src --example_commit b534f03eecd8a109db2b085ab24d419b6486de97

Prints the location of the git remote repo as well as the repos name seperated by a space.

  https://github.com/VirusTotal/yara.git yara

"""
import argparse
import os
import subprocess


def main():
  """Function to get a git repos information based on its commit."""
  parser = argparse.ArgumentParser(
      description='Finds a specific git repo in an oss-fuzz projects docker file.'
  )
  parser.add_argument(
      '--src_dir',
      help='The location of the oss-fuzz projects source directory',
      required=True)
  parser.add_argument(
      '--example_commit',
      help='A commit SHA refrencing the projects main repo',
      required=True)
  args = parser.parse_args()
  dir_content = os.listdir(args.src_dir)
  for single_dir in dir_content:
    full_path = os.path.join(args.src_dir, single_dir)
    if single_dir and os.path.isdir(full_path):
      if check_for_commit(
          os.path.join(args.src_dir, full_path), args.example_commit):
        print('Detected repo: %s %s' %
              (get_repo(full_path), single_dir.rstrip()))
        return
  print('No git repos with specific commit: %s found in %s' %
        (args.example_commit, args.src_dir))


def get_repo(dir_path):
  """Gets a git repo link from a specific directory in a docker image.

  Args:
    dir_path: The directory on the image where the git repo exists.

  Returns:
    The repo location or None
  """
  out, returncode = run_command(['git', 'config', '--get', 'remote.origin.url'],
                                location=dir_path,
                                check_result=True)
  if not returncode and out:
    return out.rstrip()
  return None


def check_for_commit(dir_path, example_commit):
  """Checks a directory for a specific commit.

  Args:
    dir_path: The name of the directory to test for the commit
    example_commit: The commit SHA to check for

  Returns:
    True if directory contains that commit
  """

  # Check if valid git repo
  if not os.path.exists(os.path.join(dir_path, '.git')):
    return False

  # Check if history fetch is needed
  if os.path.exists(os.path.join(dir_path, '.git', 'shallow')):
    run_command(['git', 'fetch', '--unshallow'], location=dir_path)

  # Check if commit is in history
  _, returncode = run_command(['git', 'cat-file', '-e', example_commit],
                              location=dir_path)
  return not returncode


def run_command(command, location='.', check_result=False):
  """Runs a shell command in the specified directory location.

  Args:
    command: The command as a list to be run
    location: The directory the command is run in
    check_result: Should an exception be thrown on failed command

  Returns:
    The stdout of the command, the error code

  Raises:
    RuntimeError: running a command resulted in an error
  """
  process = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=location)
  out, err = process.communicate()
  if check_result and (process.returncode or err):
    raise RuntimeError(
        'Error: %s\n running command: %s\n return code: %s\n out %s\n' %
        (err, command, process.returncode, out))
  if out is not None:
    out = out.decode('ascii')
  return out, process.returncode


if __name__ == '__main__':
  main()
