/* See LICENSE file for copyright and license details. */

#ifndef DW2_ANIM_HPP
#define DW2_ANIM_HPP

#include <stdint.h>

#include <istream>
#include <vector>

#include "utils.hpp"

struct dw2_matrix
{
	int16_t m[3][3];
	int16_t t[3];

	template <typename T, typename U>
	T to_matrix() const;
};

static_assert(sizeof(dw2_matrix) == 24);

template <typename T, typename U>
T dw2_matrix::to_matrix() const
{
	return T(fixed_to_real<U>(m[0][0], 12),
		 fixed_to_real<U>(m[0][1], 12),
		 fixed_to_real<U>(m[0][2], 12),
		 0,
		 fixed_to_real<U>(m[1][0], 12),
		 fixed_to_real<U>(m[1][1], 12),
		 fixed_to_real<U>(m[1][2], 12),
		 0,
		 fixed_to_real<U>(m[2][0], 12),
		 fixed_to_real<U>(m[2][1], 12),
		 fixed_to_real<U>(m[2][2], 12),
		 0,
		 fixed_to_real<U>(t[0], 0),
		 fixed_to_real<U>(t[1], 0),
		 fixed_to_real<U>(t[2], 0),
		 1);
}

class dw2_keyframe
{
public:
	/* Object keyframe data */
	std::vector<dw2_matrix> transforms;

	dw2_keyframe(std::istream& is, uint32_t num_frames);
};

class dw2_frame
{
public:
	/* Per frame per object keyframe indices */
	std::vector<std::vector<uint8_t>> keyframe_indices;
	uint8_t termination_mask;
	uint16_t loop_mask;

	dw2_frame(std::istream& is, uint32_t num_objects);
};

class dw2_anim
{
public:
	/* Per object keyframe data */
	std::vector<dw2_keyframe> keyframes;
	/* Per animation frame data */
	std::vector<dw2_frame> frames;
	/* Animation prefix [A-K] */
	char prefix;

	dw2_anim(std::istream& is, uint32_t num_objects, char prefix);
};

#endif
