/* See LICENSE file for copyright and license details. */

#include <stdint.h>

#include <map>
#include <utility>
#include <vector>

#include "clut_map.hpp"
#include "dw2_model.hpp"

clut_map::clut_map(uint32_t width, uint32_t height, uint32_t block_width,
		   uint32_t block_height)
	: m_image(width, height),
	  m_block_width(block_width),
	  m_block_height(block_height)
{
}

uint32_t clut_map::at(uint32_t x, uint32_t y) const
{
	return m_image.at(x, y);
}

void clut_map::apply_model(const dw2_model& model)
{
	for (const dw2_model_object& object : model.objects)
	{
		for (const dw2_face& face : object.faces)
		{
			uint32_t clut = (face.clut |
					 (face.stp ? DW2_CLUT_FLAG_STP : 0));

			m_image.fill_triangle(
				(face.uvs[2].x * m_image.width()) / 255,
				(face.uvs[2].y * m_image.height()) / 255,
				(face.uvs[1].x * m_image.width()) / 255,
				(face.uvs[1].y * m_image.height()) / 255,
				(face.uvs[0].x * m_image.width()) / 255,
				(face.uvs[0].y * m_image.height()) / 255,
				clut);
		}
	}

	update_blocks();
}

void clut_map::update_blocks()
{
	uint32_t blocks_w = m_image.width() / m_block_width;
	uint32_t blocks_h = m_image.height() / m_block_height;

	for (uint32_t block_x = 0; block_x < blocks_w; block_x++)
	{
		for (uint32_t block_y = 0; block_y < blocks_h; block_y++)
		{
			m_image.fill_rectangle(
				block_x * m_block_width,
				block_y * m_block_height,
				(block_x + 1) * m_block_width - 1,
				(block_y + 1) * m_block_height - 1,
				get_block_clut(block_x, block_y));
		}
	}
}

uint32_t clut_map::get_block_clut(uint32_t block_x, uint32_t block_y) const
{
	std::map<uint32_t, uint32_t> count;

	for (uint32_t x = 0; x < m_block_width; x++)
	{
		for (uint32_t y = 0; y < m_block_height; y++)
		{
			uint32_t value =
				m_image.at(block_x * m_block_width + x,
					   block_y * m_block_height + y);
			if (value != 0xffffffff)
			{
				++count[value];
			}
		}
	}

	std::pair<uint32_t, uint32_t> best_entry(0xffffffff, 0);
	for (std::pair<uint32_t, uint32_t> entry : count)
	{
		if (entry.second > best_entry.second)
		{
			best_entry = entry;
		}
	}

	return best_entry.first;
}
