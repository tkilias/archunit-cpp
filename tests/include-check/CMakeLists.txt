cmake_minimum_required(VERSION 3.20)
project(include_check_demo LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(include_check_demo src/main.cpp)
target_compile_features(include_check_demo PRIVATE cxx_std_17)
target_include_directories(include_check_demo PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
