project("pyterra")

include_directories(${PYTHON_INCLUDE_PATH})

set(PYTERRA_SOURCES
  pyterra.cxx
  pyhello.cxx pyhello.h
  )

pybind11_add_module(pyterra ${PYTERRA_SOURCES})
target_link_libraries(pyterra PUBLIC hello)
set_target_properties(pyterra PROPERTIES OUTPUT_NAME "_terra")

add_subdirectory(tests)

execute_process(
  COMMAND "${PYTHON_EXECUTABLE}" -c "if True:
    from distutils import sysconfig as sc
    print(sc.get_python_lib(plat_specific=True))"
  OUTPUT_VARIABLE PYTHON_SITE_DEFAULT
  OUTPUT_STRIP_TRAILING_WHITESPACE)
set(PYTHON_SITE "${PYTHON_SITE_DEFAULT}" CACHE STRING "Python install directory")

install(TARGETS pyterra DESTINATION ${PYTHON_SITE})