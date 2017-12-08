from __future__ import print_function
from abc import ABCMeta, abstractmethod

class Storage(object):
  __metaclass__ = ABCMeta
  @abstractmethod
  def store(self, path):
    pass
  @abstractmethod
  def load(self, path):
    pass

class Local(Storage):
  def __init__(self, base_path):
    self.base_path = base_path

  def store(self, path):
    pass

  def load(self, path):
    pass

class Manta(Storage):
  def __init__(self, base_path, private_key_content):
    self.base_path = base_path
    self.private_key_content = private_key_content

  def store(self, path):
    pass

  def load(self, path):
    pass