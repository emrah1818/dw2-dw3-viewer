/* See LICENSE file for copyright and license details. */

#include <stdint.h>

#include <algorithm>
#include <istream>
#include <vector>

#include "dw2_anim.hpp"
#include "utils.hpp"

dw2_keyframe::dw2_keyframe(std::istream& is, uint32_t num_frames)
{
	for (uint32_t i = 0; i <= num_frames; ++i)
	{
		transforms.push_back(read_sizeof<dw2_matrix>(is));
	}
}

dw2_frame::dw2_frame(std::istream& is, uint32_t num_objects)
{
	while (true)
	{
		auto ch = is.peek();
		if ((ch == 0xfe) || (ch == 0xff))
		{
			termination_mask = ch;
			break;
		}

		std::vector<uint8_t> timings;
		for (uint32_t i = 0; i < num_objects; ++i)
		{
			uint8_t keyframe = read_sizeof<uint8_t>(is);
			timings.push_back(keyframe);
		}

		keyframe_indices.push_back(timings);
	}

	termination_mask = read_sizeof<uint8_t>(is);
	loop_mask = read_sizeof<uint16_t>(is);
}

dw2_anim::dw2_anim(std::istream& is, uint32_t num_objects, char prefix)
	: prefix(prefix)
{
	/* Always zero */
	read_sizeof<uint32_t>(is);

	std::vector<uint32_t> keyframe_offsets;
	for (uint32_t i = 0; i < num_objects; ++i)
	{
		keyframe_offsets.push_back(read_sizeof<uint32_t>(is));
	}

	/* Padding */
	uint32_t offset;
	while (!(offset = read_sizeof<uint32_t>(is)));

	std::vector<uint32_t> frame_offsets;
	for (; offset && (offset != 1); offset = read_sizeof<uint32_t>(is))
	{
		frame_offsets.push_back(offset);
	}

	for (uint32_t frame_offset : frame_offsets)
	{
		is.seekg(frame_offset);
		dw2_frame frame = dw2_frame(is, num_objects);
		frames.push_back(frame);
	}

	for (uint32_t i = 0; i < num_objects; ++i)
	{
		uint8_t num_keyframes = 0;
		for (const dw2_frame& frame : frames)
		{
			for (const std::vector<uint8_t>& indices :
			     frame.keyframe_indices)
			{
				num_keyframes =
					std::max(num_keyframes, indices[i]);
			}
		}

		is.seekg(keyframe_offsets[i]);
		keyframes.push_back(dw2_keyframe(is, num_keyframes));
	}
}
