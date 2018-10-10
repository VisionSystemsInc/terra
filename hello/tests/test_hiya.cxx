#include <iostream>
#include <testlib/testlib_test.h>

#include <hello/hi.hxx>

using namespace std;

static void test_hiya()
{
  vgl_point_2d<double> x(11,22);

  vgl_point_3d<double> y = dummy_2_to_3(x);

  bool good = (y.x() == 11.0f);
  good &= (y.y() == 22.0f);
  good &= (y.z() == 1.0f);

  good &= (foo() == 1);

  TEST("hiya", good, true);
}

TESTMAIN(test_hiya);