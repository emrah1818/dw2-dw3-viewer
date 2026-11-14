/* See LICENSE file for copyright and license details. */

#ifndef DW2_MODEL_HPP
#define DW2_MODEL_HPP

#include <stdint.h>

#include <istream>
#include <vector>

struct dw2_texcoord
{
	uint8_t x;
	uint8_t y;
};

static_assert(sizeof(dw2_texcoord) == 2);

struct dw2_svec3
{
	int16_t x;
	int16_t y;
	int16_t z;
};

static_assert(sizeof(dw2_svec3) == 6);

struct dw2_quad
{
	uint8_t vertex_indices[4];
	uint8_t normal_indices[4];
	dw2_texcoord uvs[4];
	uint16_t clut;
	uint16_t mixture_rate;
};

static_assert(sizeof(dw2_quad) == 20);

struct dw2_triangle
{
	uint8_t vertex_indices[3];
	uint8_t normal_indices[3];
	dw2_texcoord uvs[3];
	uint16_t clut;
	uint16_t mixture_rate;
};

static_assert(sizeof(dw2_triangle) == 16);

struct dw2_model_header
{
	uint32_t tim_start;
	uint32_t tim_end;
	uint32_t num_objects;
};

static_assert(sizeof(dw2_model_header) == 12);

struct dw2_face
{
	uint8_t vertex_indices[3];
	uint8_t normal_indices[3];
	dw2_texcoord uvs[3];
	uint16_t clut;
	uint16_t mixture_rate;
	bool stp;
};

class dw2_model_object
{
public:
	std::vector<dw2_svec3> vertices;
	std::vector<dw2_svec3> normals;
	std::vector<dw2_face> faces;
	bool has_stp_faces;
	bool has_opaque_faces;

	dw2_model_object(std::istream& is, uint32_t vertex_offset,
			 uint32_t normal_offset, uint32_t primitive_offset);
};

class dw2_model
{
public:
	std::vector<dw2_model_object> objects;
	std::vector<uint32_t> skeleton;
	std::vector<uint8_t> texture;
	std::vector<uint16_t> clut;
	uint8_t blinking_data[24];

	dw2_model(std::istream& is);

private:
	void read_tim(std::istream& is, uint32_t tim_start);
};

#endif
