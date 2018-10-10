#include <vgl/vgl_point_2d.h>
#include <vgl/vgl_point_3d.h>

template <class T>
vgl_point_3d<T> dummy_2_to_3(vgl_point_2d<T> &d);
int foo();

template <class T>
vgl_point_3d<T> dummy_2_to_3(vgl_point_2d<T> &d)
{
  return vgl_point_3d<T>(d.x(), d.y(), 1.0);
}