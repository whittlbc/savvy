class FallbackLogger(object):
  """Fallback logger class with info/warn/error methods which all simply map to print()"""
  def __init__(self):
    [setattr(self, method, print) for method in ('info', 'warn', 'error')]


fallback_logger = FallbackLogger()