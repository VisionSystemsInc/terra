project("hello")

set(HELLO_SOURCES
  hi.cxx  hi.hxx
)

add_library(hello ${HELLO_SOURCES})
target_link_libraries(hello vgl)

add_subdirectory(tests)
