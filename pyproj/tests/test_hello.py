#!/usr/bin/env python
import unittest
import vxl
import proj

class TestHello(unittest.TestCase):

  def test_foo(self):
    self.assertEqual(proj.hello.foo(), 1)

  def test_dummy(self):
    p2 = vxl.vgl.point_2d(11, 22)
    p3 = proj.hello.dummy_2_to_3(p2)
    self.assertEqual(p3.x, 11)
    self.assertEqual(p3.y, 22)
    self.assertEqual(p3.z, 1)