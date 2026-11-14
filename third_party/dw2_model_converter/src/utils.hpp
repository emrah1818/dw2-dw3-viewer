/* See LICENSE file for copyright and license details. */

#ifndef DW2_UTILS_HPP
#define DW2_UTILS_HPP

#include <stdint.h>

#include <istream>
#include <ostream>

#define DW2_ARRAY_SIZE(a)	(sizeof(a) / sizeof(*(a)))

template <typename T>
T fixed_to_real(int16_t value, uint32_t decimal_bits)
{
	return (T)value / (1 << decimal_bits);
}

template <typename T>
T read_sizeof(std::istream& is)
{
	T t;

	is.read(reinterpret_cast<char*>(&t), sizeof(T));

	return t;
}

void stream_copy(std::istream& is, std::ostream& os, size_t bytes);

#endif
