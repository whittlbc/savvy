import re
import sys
from savvy.internal.fallback_logger import fallback_logger
from subprocess import Popen, PIPE


class Shell(object):
  """
  Class providing methods for secure sys calls with automatic error handling and log management.

  Basic usage:
    shell = Shell()

    # Execute a command
    status, stdout, stderr = shell.exec(('cat', 'setup.py'))

    # Execute a command where you only care if it succeeds or not
    dir_creation_successful = shell.bool_exec(('mkdir', 'my-dir'))
  """

  def __init__(self, logger=fallback_logger, bufsize=-1,
               stdout=PIPE, stderr=PIPE, creationflags=0):
    """
    :param logger: logging class instance or module to use for logging errors/warnings/etc.

    :param int bufsize:
        supplied as the buffering argument to the open() function when
        creating the stdin/stdout/stderr pipe file objects

    :param int stdout: stdout file handle
    :param int stderr: stderr file handle
    :param int creationflags: Windows only
    """
    self.logger = logger
    self.bufsize = bufsize
    self.stdout = stdout
    self.stderr = stderr
    self.creationflags = creationflags
    self.default_err_status = 1

  def exec(self, cmd, bufsize=None, stdout=None,
           stderr=None, creationflags=None, **subprocess_kwargs):
    """
    Makes a sys call and consumes/returns the status, stdout, and stderr.

    :param list/tuple cmd:
        The command argument sequence to execute. The program to execute is
        the first item in the sequence.

    :param int bufsize:
        Supplied as the buffering argument to the open() function when
        creating the stdin/stdout/stderr pipe file objects.

    :param int stdout: stdout file handle
    :param int stderr: stderr file handle
    :param int creationflags: Windows only
    :param dict subprocess_kwargs: Keyword arguments to be passed to subprocess.Popen

    :return: the status, stdout, and stderr for the provided cmd, respectively
    :rtype: tuple(int, str, str)
    """
    # Use class defaults as backups.
    if bufsize is None: bufsize = self.bufsize
    if stdout is None: stdout = self.stdout
    if stderr is None: stderr = self.stderr
    if creationflags is None: creationflags = self.creationflags

    try:
      # Ensure command components are free of sub/nested-commands.
      self._validate_cmd_comps(cmd)
    except (ValueError, UserWarning) as e:
      self.logger.error(str(e))
      return self.default_err_status, '', str(e)

    # Set initial return values.
    status = 0
    stdout_value = b''
    stderr_value = b''

    try:
      # Execute the provided command.
      process = Popen(cmd, bufsize=bufsize, stdout=stdout, stderr=stderr,
                      creationflags=creationflags, **subprocess_kwargs)
    except OSError as e:
      self.logger.error('OS Error occurred during command call "{}": {}.'.format(' '.join(cmd), str(e)))
      return self.default_err_status, stdout_value, stderr_value

    try:
      # Read stdout, stderr, and the return status of the command.
      stdout_value, stderr_value = process.communicate()

      # Safely decode any binary strings & strip any leading/trailing new lines.
      stdout_value = self._safe_decode(stdout_value.strip())
      stderr_value = self._safe_decode(stderr_value.strip())

      # Note the command return status.
      status = process.returncode
    finally:
      # Close stdout/stderr pipes.
      process.stdout.close()
      process.stderr.close()

    return status, stdout_value, stderr_value

  def bool_exec(self, cmd, **kwargs):
    """
    Get bool representation of whether or not a provided cmd succeeds.

    :param list/tuple cmd:
        The command argument sequence to execute. The program to execute is
        the first item in the sequence.

    :param dict kwargs: Keyword arguments to be passed to self.exec

    :return: bool representation of whether or not a provided cmd succeeds
    :rtype: bool
    """
    try:
      status, stdout, stderr = self.exec(cmd, **kwargs)
    except BaseException as e:
      self.logger.error('Command "{}" failed with unknown error: {}.'.format(' '.join(cmd), str(e)))
      return False

    if status != 0:
      self.logger.error('Command "{}" returned non-zero status({}) with error: {}.'.format(' '.join(cmd), status, stderr))
      return False

    return True

  def _validate_cmd_comps(self, cmd):
    """
    Validate that no sub/nested-commands exist in a command args sequence.
    Will raise error if so.

    :param list/tuple cmd: command argument sequence
    """
    for comp in cmd:
      if not comp:
        raise ValueError('Empty item found in command "{}".'.format(' '.join(cmd)))

      if re.match('\$\(.*\)', str(comp)):
        raise UserWarning('Invalid command -- attempted subcommand "{}" within full command "{}".'.format(comp, ' '.join(cmd)))

  def _safe_decode(self, s):
    """Safely decodes a binary string to unicode"""
    if isinstance(s, bytes):
      return s.decode(sys.getdefaultencoding(), 'surrogateescape')
    else:
      return s


# Vanilla shell instance available for import
shell = Shell()