/* See LICENSE file for copyright and license details. */

#ifndef DW2_IMAGE_HPP
#define DW2_IMAGE_HPP

#include <assert.h>
#include <stdint.h>

#include <algorithm>
#include <utility>
#include <vector>

template <typename T>
class image
{
public:
	image(uint32_t width, uint32_t height, T value = 0xffffffff);
	image(const T* data, uint32_t width, uint32_t height);

	const T& at(uint32_t x, uint32_t y) const;
	T& at(uint32_t x, uint32_t y);

	uint32_t width() const;
	uint32_t height() const;

	void fill(T value);

	void fill_rectangle(uint32_t x0, uint32_t y0, uint32_t x1,
			    uint32_t y1, T value);

	void fill_triangle(uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1,
			   uint32_t x2, uint32_t y2, T value);

private:
	std::vector<T> m_data;
	uint32_t m_width;
	uint32_t m_height;
};

class line_iterator
{
public:
	line_iterator(int32_t x0, int32_t y0, int32_t x1, int32_t y1);

	operator bool() const;
	line_iterator& operator++();
	line_iterator operator++(int);

	int32_t x() const;
	int32_t y() const;

protected:
	int32_t m_x;
	int32_t m_y;
	int32_t m_x1;
	int32_t m_y1;
	int32_t m_dx;
	int32_t m_dy;
	int32_t m_sx;
	int32_t m_sy;
	int32_t m_e;

	virtual void next();
};

class line_y_iterator : public line_iterator
{
public:
	line_y_iterator(int32_t x0, int32_t y0, int32_t x1, int32_t y1);

private:
	void next() override;
};

template <typename T>
image<T>::image(uint32_t width, uint32_t height, T value)
	: m_data(width * height, value),
	  m_width(width),
	  m_height(height)
{
}

template <typename T>
image<T>::image(const T* data, uint32_t width, uint32_t height)
	: m_data(data, data + (width * height)),
	  m_width(width),
	  m_height(height)
{
}

template <typename T>
uint32_t image<T>::width() const
{
	return m_width;
}

template <typename T>
uint32_t image<T>::height() const
{
	return m_height;
}

template <typename T>
const T& image<T>::at(uint32_t x, uint32_t y) const
{
	assert((x < m_width) && (y < m_height));

	return m_data.at(y * m_width + x);
}

template <typename T>
T& image<T>::at(uint32_t x, uint32_t y)
{
	assert((x < m_width) && (y < m_height));

	return m_data.at(y * m_width + x);
}

template <typename T>
void image<T>::fill(T value)
{
	std::fill(m_data.begin(), m_data.end(), value);
}

template <typename T>
void image<T>::fill_rectangle(uint32_t x0, uint32_t y0, uint32_t x1,
			      uint32_t y1, T value)
{
	uint32_t min_x = std::min(x0, x1);
	uint32_t min_y = std::min(y0, y1);
	uint32_t max_x = std::max(x0, x1);
	uint32_t max_y = std::max(y0, y1);

	for (uint32_t j = min_y; j <= max_y; ++j)
	{
		for (uint32_t i = min_x; i <= max_x; ++i)
		{
			at(i, j) = value;
		}
	}
}

template <typename T>
void image<T>::fill_triangle(uint32_t x0, uint32_t y0, uint32_t x1,
			     uint32_t y1, uint32_t x2, uint32_t y2, T value)
{
	if (y0 > y1)
	{
		std::swap(x0, x1);
		std::swap(y0, y1);
	}

	if (y0 > y2)
	{
		std::swap(x0, x2);
		std::swap(y0, y2);
	}

	if (y1 > y2)
	{
		std::swap(x1, x2);
		std::swap(y1, y2);
	}

	/* Fill inside of triangle */
	line_y_iterator l0(x0, y0, x1, y1);
	line_y_iterator l1(x0, y0, x2, y2);

	for (; l0 && l1; ++l0, ++l1)
	{
		fill_rectangle(l0.x(), l0.y(), l1.x(), l0.y(), value);
	}

	l0 = line_y_iterator(x1, y1, x2, y2);

	for (; l0 && l1; ++l0, ++l1)
	{
		fill_rectangle(l0.x(), l0.y(), l1.x(), l0.y(), value);
	}

	fill_rectangle(l0.x(), l0.y(), l1.x(), l0.y(), value);

	/* Draw triangle outline */
	line_iterator l = line_iterator(x0, y0, x1, y1);
	for (; l; ++l)
	{
		at(l.x(), l.y()) = value;
	}

	at(l.x(), l.y()) = value;

	l = line_iterator(x0, y0, x2, y2);
	for (; l; ++l)
	{
		at(l.x(), l.y()) = value;
	}

	at(l.x(), l.y()) = value;

	l = line_iterator(x1, y1, x2, y2);
	for (; l; ++l)
	{
		at(l.x(), l.y()) = value;
	}

	at(l.x(), l.y()) = value;
}

#endif
