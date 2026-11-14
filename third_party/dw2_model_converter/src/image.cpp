/* See LICENSE file for copyright and license details. */

#include <math.h>

#include "image.hpp"

line_iterator::line_iterator(int32_t x0, int32_t y0, int32_t x1, int32_t y1)
{
	m_x = x0;
	m_y = y0;
	m_x1 = x1;
	m_y1 = y1;
	m_dx = abs((long)(x1 - x0));
	m_dy = -abs((long)(y1 - y0));
	m_sx = x0 < x1 ? 1 : -1;
	m_sy = y0 < y1 ? 1 : -1;
	m_e = m_dx + m_dy;
}

line_iterator::operator bool() const
{
	return !((m_x == m_x1) && (m_y == m_y1));
}

line_iterator& line_iterator::operator++()
{
	next();

	return *this;
}

line_iterator line_iterator::operator++(int)
{
	line_iterator it = *this;

	++*this;

	return it;
}

int32_t line_iterator::x() const
{
	return m_x;
}

int32_t line_iterator::y() const
{
	return m_y;
}

void line_iterator::next()
{
	while (*this)
	{
		int32_t e2 = m_e * 2;
		if (e2 > m_dy)
		{
			m_e += m_dy;
			m_x += m_sx;
			break;
		}
		if (e2 < m_dx)
		{
			m_e += m_dx;
			m_y += m_sy;
			break;
		}
	}
}

line_y_iterator::line_y_iterator(int32_t x0, int32_t y0, int32_t x1,
				 int32_t y1)
	: line_iterator(x0, y0, x1, y1)
{
}

void line_y_iterator::next()
{
	while (*this)
	{
		int32_t e2 = m_e * 2;
		if (e2 > m_dy)
		{
			m_e += m_dy;
			m_x += m_sx;
		}
		if (e2 < m_dx)
		{
			m_e += m_dx;
			m_y += m_sy;
			break;
		}
	}
}
