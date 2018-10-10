project("pyproj")

include_directories(${PYTHON_INCLUDE_PATH})

set(PYPROJ_SOURCES
  pyproj.cxx
  pyhello.cxx pyhello.h
  )

pybind11_add_module(pyproj ${PYPROJ_SOURCES})
target_link_libraries(pyproj PUBLIC hello)
set_target_properties(pyproj PROPERTIES OUTPUT_NAME "proj")

execute_process(
  COMMAND "${PYTHON_EXECUTABLE}" -c "if True:
    from distutils import sysconfig as sc
    print(sc.get_python_lib(plat_specific=True))"
  OUTPUT_VARIABLE PYTHON_SITE_DEFAULT
  OUTPUT_STRIP_TRAILING_WHITESPACE)
set(PYTHON_SITE "${PYTHON_SITE_DEFAULT}" CACHE STRING "Python install directory")

install(TARGETS pyproj DESTINATION ${PYTHON_SITE})