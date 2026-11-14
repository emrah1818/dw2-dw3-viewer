/* See LICENSE file for copyright and license details. */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include <istream>
#include <vector>

#include "dw2_model.hpp"
#include "utils.hpp"

std::vector<dw2_face> to_faces(const dw2_quad& quad, bool stp)
{
	std::vector<dw2_face> faces;

	dw2_face face0;
	face0.vertex_indices[0] = quad.vertex_indices[0];
	face0.vertex_indices[1] = quad.vertex_indices[1];
	face0.vertex_indices[2] = quad.vertex_indices[2];
	face0.normal_indices[0] = quad.normal_indices[0];
	face0.normal_indices[1] = quad.normal_indices[1];
	face0.normal_indices[2] = quad.normal_indices[2];
	face0.uvs[0] = quad.uvs[0];
	face0.uvs[1] = quad.uvs[1];
	face0.uvs[2] = quad.uvs[2];
	face0.clut = quad.clut;
	face0.mixture_rate = quad.mixture_rate;
	face0.stp = stp;
	faces.push_back(face0);

	dw2_face face1;
	face1.vertex_indices[0] = quad.vertex_indices[3];
	face1.vertex_indices[1] = quad.vertex_indices[2];
	face1.vertex_indices[2] = quad.vertex_indices[1];
	face1.normal_indices[0] = quad.normal_indices[3];
	face1.normal_indices[1] = quad.normal_indices[2];
	face1.normal_indices[2] = quad.normal_indices[1];
	face1.uvs[0] = quad.uvs[3];
	face1.uvs[1] = quad.uvs[2];
	face1.uvs[2] = quad.uvs[1];
	face1.clut = quad.clut;
	face1.mixture_rate = quad.mixture_rate;
	face1.stp = stp;
	faces.push_back(face1);

	return faces;
}

dw2_face to_face(const dw2_triangle& triangle, bool stp)
{
	dw2_face face;
	face.vertex_indices[0] = triangle.vertex_indices[0];
	face.vertex_indices[1] = triangle.vertex_indices[1];
	face.vertex_indices[2] = triangle.vertex_indices[2];
	face.normal_indices[0] = triangle.normal_indices[0];
	face.normal_indices[1] = triangle.normal_indices[1];
	face.normal_indices[2] = triangle.normal_indices[2];
	face.uvs[0] = triangle.uvs[0];
	face.uvs[1] = triangle.uvs[1];
	face.uvs[2] = triangle.uvs[2];
	face.clut = triangle.clut;
	face.mixture_rate = triangle.mixture_rate;
	face.stp = stp;

	return face;
}

dw2_model_object::dw2_model_object(std::istream& is, uint32_t vertex_offset,
				   uint32_t normal_offset,
				   uint32_t primitive_offset)
	: has_stp_faces(false),
	  has_opaque_faces(false)
{
	is.seekg(vertex_offset);

	uint32_t num_vertices = read_sizeof<uint32_t>(is);
	read_sizeof<uint16_t>(is);

	for (uint32_t i = 0; i < num_vertices; ++i)
	{
		vertices.push_back(read_sizeof<dw2_svec3>(is));
	}

	is.seekg(normal_offset);

	uint32_t num_normals = read_sizeof<uint32_t>(is);
	read_sizeof<uint16_t>(is);

	for (uint32_t i = 0; i < num_normals; ++i)
	{
		normals.push_back(read_sizeof<dw2_svec3>(is));
	}

	is.seekg(primitive_offset);

	uint32_t num_primitives;

	/* Semi-transparent quads */
	num_primitives = read_sizeof<uint32_t>(is);
	for (uint32_t i = 0; i < num_primitives; ++i)
	{
		dw2_quad quad = read_sizeof<dw2_quad>(is);

		std::vector<dw2_face> f = to_faces(quad, true);
		faces.insert(faces.end(), f.begin(), f.end());

		has_stp_faces = true;
	}

	/* Opaque quads */
	num_primitives = read_sizeof<uint32_t>(is);
	for (uint32_t i = 0; i < num_primitives; ++i)
	{
		dw2_quad quad = read_sizeof<dw2_quad>(is);

		std::vector<dw2_face> f = to_faces(quad, false);
		faces.insert(faces.end(), f.begin(), f.end());

		has_opaque_faces = true;
	}

	/* Semi-transparent triangles */
	num_primitives = read_sizeof<uint32_t>(is);
	for (uint32_t i = 0; i < num_primitives; ++i)
	{
		dw2_triangle triangle = read_sizeof<dw2_triangle>(is);
		faces.push_back(to_face(triangle, true));

		has_stp_faces = true;
	}

	/* Opaque triangles */
	num_primitives = read_sizeof<uint32_t>(is);
	for (uint32_t i = 0; i < num_primitives; ++i)
	{
		dw2_triangle triangle = read_sizeof<dw2_triangle>(is);
		faces.push_back(to_face(triangle, false));

		has_opaque_faces = true;
	}

	assert(!faces.empty());

	/* Assert all faces have the same mixture rate */
	for (size_t i = 1; i < faces.size(); ++i)
	{
		assert(faces[i].mixture_rate == faces[0].mixture_rate);
	}
}

dw2_model::dw2_model(std::istream& is)
{
	dw2_model_header header = read_sizeof<dw2_model_header>(is);

	std::vector<uint32_t> vertex_offsets;
	std::vector<uint32_t> normal_offsets;
	std::vector<uint32_t> primitive_offsets;

	for (size_t i = 0; i < header.num_objects; ++i)
	{
		vertex_offsets.push_back(read_sizeof<uint32_t>(is));
	}

	for (size_t i = 0; i < header.num_objects; ++i)
	{
		normal_offsets.push_back(read_sizeof<uint32_t>(is));
	}

	for (size_t i = 0; i < header.num_objects; ++i)
	{
		primitive_offsets.push_back(read_sizeof<uint32_t>(is));
	}

	for (size_t i = 0; i < header.num_objects; ++i)
	{
		skeleton.push_back(read_sizeof<uint32_t>(is));
	}

	is.read(reinterpret_cast<char*>(blinking_data),
		sizeof(blinking_data));

	for (size_t i = 0; i < header.num_objects; ++i)
	{
		objects.push_back(dw2_model_object(is, vertex_offsets[i],
						   normal_offsets[i],
						   primitive_offsets[i]));
	}

	read_tim(is, header.tim_start);
}

void dw2_model::read_tim(std::istream& is, uint32_t tim_start)
{
	uint32_t value;

	is.seekg(tim_start);

	/* ID */
	value = read_sizeof<uint32_t>(is);
	assert(value == 0x10);

	/* FLAG */
	value = read_sizeof<uint32_t>(is);
	assert(value & (1 << 3));

	/* CLUT bnum */
	value = read_sizeof<uint32_t>(is);
	assert(value == 44);

	/* CLUT DX, DY */
	read_sizeof<uint32_t>(is);

	/* CLUT W, H */
	value = read_sizeof<uint32_t>(is);
	assert(value == 0x00010100);

	/* Skip unused CLUT */
	is.seekg(16 * sizeof(uint16_t), std::ios_base::cur);

	/* Pixel bnum */
	value = read_sizeof<uint32_t>(is);
	assert(value == 16396);

	/* Pixel DX, DY */
	read_sizeof<uint32_t>(is);

	/* Pixel W, H */
	uint32_t dimensions = read_sizeof<uint32_t>(is);
	assert(dimensions == 0x01000020);

	/* DATA */
	for (size_t i = 0; i < value - sizeof(uint32_t) * 3; ++i)
	{
		texture.push_back(read_sizeof<uint8_t>(is));
	}

	/* Read CLUT from end of texture */
	is.seekg(tim_start + 0x4040 - 1024 * sizeof(uint16_t));

	for (size_t i = 0; i < 1024; ++i)
	{
		clut.push_back(read_sizeof<uint16_t>(is));
	}
}
