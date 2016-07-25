#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import ctypes


BITS_64 = 0xFFFFFFFFFFFFFFFF
BITS_32 = 0xFFFFFFFF
FIRST_BIT_64 = 1 << 63


def to_psql_int64(i):
  """Converts a given 64-bit unsigned integer value to a signed integer
  for storage in postgres.

  >>> to_psql_int64(1)
  1
  >>> to_psql_int64(1 << 32)
  4294967296
  >>> to_psql_int64(1 << 63)
  -9223372036854775808
  """
  if i < 0:
    return i
  # psql has no unsigned integers, so if the first bit is flipped here,
  # return the very large number as a negative integer.
  if i & FIRST_BIT_64:
    return ctypes.c_longlong(i).value
  return i



def reverse_bits(i, number_of_bits=64):
  """Reverse the bits in this number.

  >>> reverse_bits(1)
  9223372036854775808L
  >>> bin(reverse_bits(0b110, 8))
  '0b1100000'
  >>> bin(reverse_bits(0b1, 4))
  '0b1000'
  """
  bitmask = flipped_bits_64(number_of_bits)
  # Clean up any negative values so they become large positive numbers
  binary_string = bin(i & bitmask)[2:]
  if len(binary_string) < number_of_bits:
    num_needed_zeroes = number_of_bits - len(binary_string)
    needed_zeroes = '0000000000000000000000000000000000000000000000000000000000000000'[:num_needed_zeroes]
    binary_string = needed_zeroes + binary_string

  return int(''.join(reversed(binary_string)), 2)


def num_bits_64(i):
  """Counts the bits in a given integer.

  >>> num_bits_64(7)
  3
  >>> num_bits_64(8)
  1
  >>> num_bits_64(0b1100110000000000000000000000000)
  4
  """
  # & here converts negative integers to unsigned representation first,
  # so we get the correct number of bits.
  return bin(i & BITS_64).count('1')


def wrapping_right_shift_64(i, offset):
  """Shifts a given 64-bit bitmask by offset, preserving the wrapped bits on
  the start of the resulting bitmask.

  >>> wrapping_right_shift_64(0b1000, 3)
  1L
  >>> wrapping_right_shift_64(0b1, -3)
  8L
  >>> wrapping_right_shift_64(0b1000, 4)
  9223372036854775808L
  >>> wrapping_right_shift_64(0b1000000000000000000000000000000000000000000000000000000000000111, 63)
  15L
  >>> bin(wrapping_right_shift_64(0b1100111000111100001111100000111111000000111111100000001111111000, 32))
  '0b1100000011111110000000111111100011001110001111000011111000001111'
  >>> bin(wrapping_right_shift_64(0b1001100000000000000000000000000000000000000000000000000000000001, -30))
  '0b1100110000000000000000000000000'
  >>> bin(wrapping_right_shift_64(0b1, -65))
  '0b10'
  """
  offset = offset % 64
  end = i >> offset
  start = (i << (64 - offset)) & BITS_64
  return end | start


def flipped_bits_64(length):
  """Produces a 1-bit bitmask of given length.

  >>> flipped_bits_64(3)
  7
  >>> flipped_bits_64(1)
  1
  >>> bin(flipped_bits_64(68))
  '0b1111111111111111111111111111111111111111111111111111111111111111'
  """
  return 2 ** min(length, 64) - 1


def trailing_window_bitmask_64(offset, window_size):
  """Produces a 64-bit bitmask of window_size 1-bits, wrapping around a 64-bit
  int starting at bit offset.

  >>> trailing_window_bitmask_64(1, 1)
  1L
  >>> bin(trailing_window_bitmask_64(0, 3))
  '0b1110000000000000000000000000000000000000000000000000000000000000'
  >>> bin(trailing_window_bitmask_64(3, 3))
  '0b111'
  >>> bin(trailing_window_bitmask_64(63, 4))
  '0b111100000000000000000000000000000000000000000000000000000000000'
  >>> bin(trailing_window_bitmask_64(66, 4))
  '0b1100000000000000000000000000000000000000000000000000000000000011'
  """
  window_bits = flipped_bits_64(window_size)
  return wrapping_right_shift_64(window_bits, window_size - offset)
