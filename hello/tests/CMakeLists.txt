
add_executable( hello_test_all
  test_driver.cxx
  test_hiya.cxx
)

target_link_libraries( hello_test_all hello) # testlib) #vnl
add_test(NAME hello_test_hiya COMMAND $<TARGET_FILE:hello_test_all> test_hiya)

install(TARGETS hello_test_all DESTINATION bin)

