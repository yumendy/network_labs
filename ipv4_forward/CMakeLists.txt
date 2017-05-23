cmake_minimum_required(VERSION 3.7)
project(ipv4_forward)

set(CMAKE_CXX_STANDARD 11)

set(SOURCE_FILES main.cpp)
add_executable(ipv4_forward ${SOURCE_FILES})