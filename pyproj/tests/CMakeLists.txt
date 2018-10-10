
add_test(NAME pyproj COMMAND python -m unittest discover ${CMAKE_SOURCE_DIR}/pyproj/tests)
set_property(TEST pyproj
      APPEND PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/pyproj-build:${CMAKE_BINARY_DIR}/pyvxl-build
      )
