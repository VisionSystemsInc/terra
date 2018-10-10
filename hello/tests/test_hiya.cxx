#include <iostream>
#include <testlib/testlib_test.h>

using namespace std;

static void test_hiya()
{
  cout << "Hi" << endl;

  TEST("hiya", true, true);
}

TESTMAIN(test_hiya);