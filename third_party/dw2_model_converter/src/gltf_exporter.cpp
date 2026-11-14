/* See LICENSE file for copyright and license details. */

#include <assert.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>

#include <algorithm>
#include <iterator>
#include <map>
#include <string>
#include <vector>

#define GLM_ENABLE_EXPERIMENTAL
#include <glm/glm.hpp>
#include <glm/gtx/matrix_decompose.hpp>
#include <glm/gtx/quaternion.hpp>
#include <tiny_gltf.h>

#include "clut_map.hpp"
#include "dw2_anim.hpp"
#include "dw2_model.hpp"
#include "gltf_exporter.hpp"
#include "image.hpp"
#include "utils.hpp"

bool operator<(const material_mode& lhs, const material_mode& rhs)
{
	return ((!lhs.stp && rhs.stp) ||
		(lhs.stp && rhs.stp &&
		 (lhs.mixture_rate < rhs.mixture_rate)));
}

template <typename T>
int push(std::vector<T>& vec, T& val)
{
	size_t id = vec.size();
	assert(id < INT_MAX);

	vec.push_back(val);

	return (int)id;
}

gltf_exporter::gltf_exporter(const dw2_model& model,
			     const std::vector<dw2_anim>& anims)
	: m_dw2_model(model),
	  m_anims(anims)
{
	build_asset_entry();
	build_scene();
	build_animations();
	build_texture();
}

bool gltf_exporter::save(const std::string& filename)
{
	tinygltf::TinyGLTF gltf;

	return gltf.WriteGltfSceneToFile(&m_gltf_model, filename, true, true,
					 true, false);
}

void gltf_exporter::build_asset_entry()
{
	m_gltf_model.asset.version = "2.0";
	m_gltf_model.asset.generator = (std::string(PROJECT_NAME) + " v" +
					std::string(PROJECT_VERSION));
}

std::vector<double> to_vector(const glm::dvec3& v)
{
	return {v.x, -v.y, -v.z};
}

std::vector<double> to_vector(const glm::dquat& v)
{
	return {-v.x, v.y, v.z, v.w};
}

void gltf_exporter::build_scene()
{
	tinygltf::Scene scene;

	tinygltf::Skin skin;
	skin.skeleton = 0;

	size_t skin_id = push(m_gltf_model.skins, skin);

	const dw2_anim& anim = m_anims.front();
	const std::vector<dw2_keyframe>& keyframes = anim.keyframes;
	const dw2_frame& frame = anim.frames.front();

	std::vector<size_t> object_indices(m_dw2_model.objects.size());
	std::vector<size_t> bone_indices(m_dw2_model.objects.size());

	for (size_t i = 0; i < m_dw2_model.objects.size(); ++i)
	{
		uint32_t index = frame.keyframe_indices.at(0).at(i);
		const dw2_matrix& pose = keyframes.at(i).transforms.at(index);

		glm::dmat4 transform = pose.to_matrix<glm::dmat4, double>();

		glm::dvec3 scale;
		glm::dquat orientation;
		glm::dvec3 translation;
		glm::dvec3 skew;
		glm::dvec4 perspective;
		bool result = glm::decompose(transform, scale, orientation,
					     translation, skew, perspective);
		if (!result)
		{
			scale = glm::dvec3(1.0);
			orientation = glm::dquat();
			translation = glm::dvec3();
		}

		tinygltf::Node node;
		node.name = (std::string("bone_") +
			     std::to_string(m_gltf_model.nodes.size()));
		node.translation = to_vector(translation);
		node.rotation = to_vector(orientation);
		node.scale = to_vector(scale);

		int node_id = push(m_gltf_model.nodes, node);

		uint32_t parent = m_dw2_model.skeleton.at(i);
		assert(parent < m_dw2_model.objects.size());

		if (parent)
		{
			size_t parent_index = object_indices[parent - 1];
			m_gltf_model.nodes.at(parent_index)
				.children.push_back(node_id);
			object_indices[parent] = i;
		}
		else
		{
			scene.nodes.push_back(node_id);
			object_indices[0] = i;
		}

		m_gltf_model.skins[skin_id].joints.push_back(node_id);

		bone_indices[i] = node_id;
	}

	for (size_t i = 0; i < m_dw2_model.objects.size(); ++i)
	{
		const dw2_model_object& object = m_dw2_model.objects.at(i);

		tinygltf::Mesh mesh;

		if (object.has_stp_faces)
		{
			mesh.primitives.push_back(
				build_primitives(object, true));
		}

		if (object.has_opaque_faces)
		{
			mesh.primitives.push_back(
				build_primitives(object, false));
		}

		int mesh_id = push(m_gltf_model.meshes, mesh);

		tinygltf::Node node;
		node.name = (std::string("mesh_") + std::to_string(mesh_id));
		node.mesh = mesh_id;

		int node_id = push(m_gltf_model.nodes, node);

		m_gltf_model.nodes.at(bone_indices[i])
			.children.push_back(node_id);
	}

	tinygltf::Value::Object extras;

	tinygltf::Value::Array blinking_data;
	for (size_t i = 0; i < DW2_ARRAY_SIZE(m_dw2_model.blinking_data); ++i)
	{
		uint8_t c = m_dw2_model.blinking_data[i];
		blinking_data.push_back(tinygltf::Value((int)c));
	}

	extras["blinking_data"] = tinygltf::Value(blinking_data);

	scene.extras = tinygltf::Value(extras);

	m_gltf_model.defaultScene = push(m_gltf_model.scenes, scene);
}

void gltf_exporter::build_animations()
{
	for (const dw2_anim& anim : m_anims)
	{
		for (size_t i = 0; i < anim.frames.size(); ++i)
		{
			const dw2_frame& frame = anim.frames[i];

			std::string suffix = std::string(1, anim.prefix);
			if (anim.frames.size() > 1)
			{
				suffix += std::to_string(i);
			}

			build_animation(anim.keyframes, frame, suffix);
		}
	}
}

void gltf_exporter::build_animation(
	const std::vector<dw2_keyframe>& keyframes, const dw2_frame& frame,
	const std::string& suffix)
{
	tinygltf::Animation anim;

	anim.name = std::string("anim_") + suffix;

	for (size_t i = 0; i < m_dw2_model.objects.size(); ++i)
	{
		std::vector<float> pos_time;
		std::vector<glm::vec3> pos;
		std::vector<float> rot_time;
		std::vector<glm::quat> rot;
		std::vector<float> scale_time;
		std::vector<glm::vec3> scale;

		for (size_t j = 0; j < frame.keyframe_indices.size(); ++j)
		{
			uint32_t keyframe =
				frame.keyframe_indices.at(j).at(i);
			const dw2_matrix& pose =
				keyframes.at(i).transforms.at(keyframe);

			glm::dmat4 transform =
				pose.to_matrix<glm::dmat4, double>();

			glm::dvec3 sca;
			glm::dquat orientation;
			glm::dvec3 translation;
			glm::dvec3 skew;
			glm::dvec4 perspective;
			bool result = glm::decompose(transform, sca,
						     orientation, translation,
						     skew, perspective);
			if (!result)
			{
				sca = glm::dvec3(1.0);
				orientation = glm::dquat();
				translation = glm::dvec3();
			}

			translation.y = -translation.y;
			translation.z = -translation.z;

			orientation.x = -orientation.x;

			float t = j / 30.0f;

			pos_time.push_back(t);
			pos.push_back(translation);

			rot_time.push_back(t);
			rot.push_back(orientation);

			scale_time.push_back(t);
			scale.push_back(sca);
		}

		tinygltf::AnimationChannel pos_channel;
		tinygltf::AnimationChannel rot_channel;
		tinygltf::AnimationChannel scale_channel;
		tinygltf::AnimationSampler pos_sampler;
		tinygltf::AnimationSampler rot_sampler;
		tinygltf::AnimationSampler scale_sampler;

		pos_sampler.input = build_accessor(
			pos_time, TINYGLTF_COMPONENT_TYPE_FLOAT,
			TINYGLTF_TYPE_SCALAR, 0);
		pos_sampler.interpolation = "LINEAR";
		pos_sampler.output =
			build_accessor(pos, TINYGLTF_COMPONENT_TYPE_FLOAT,
				       TINYGLTF_TYPE_VEC3, 0);

		rot_sampler.input = build_accessor(
			rot_time, TINYGLTF_COMPONENT_TYPE_FLOAT,
			TINYGLTF_TYPE_SCALAR, 0);
		rot_sampler.interpolation = "LINEAR";
		rot_sampler.output =
			build_accessor(rot, TINYGLTF_COMPONENT_TYPE_FLOAT,
				       TINYGLTF_TYPE_VEC4, 0);

		scale_sampler.input = build_accessor(
			scale_time, TINYGLTF_COMPONENT_TYPE_FLOAT,
			TINYGLTF_TYPE_SCALAR, 0);
		scale_sampler.interpolation = "LINEAR";
		scale_sampler.output =
			build_accessor(scale, TINYGLTF_COMPONENT_TYPE_FLOAT,
				       TINYGLTF_TYPE_VEC3, 0);

		pos_channel.target_node = (int)i;
		pos_channel.target_path = "translation";
		pos_channel.sampler = push(anim.samplers, pos_sampler);
		rot_channel.target_node = (int)i;
		rot_channel.target_path = "rotation";
		rot_channel.sampler = push(anim.samplers, rot_sampler);
		scale_channel.target_node = (int)i;
		scale_channel.target_path = "scale";
		scale_channel.sampler = push(anim.samplers, scale_sampler);

		push(anim.channels, pos_channel);
		push(anim.channels, rot_channel);
		push(anim.channels, scale_channel);
	}

	tinygltf::Value::Object extras;

	extras["termination_mask"] = tinygltf::Value(frame.termination_mask);
	extras["loop_mask"] = tinygltf::Value(frame.loop_mask);

	anim.extras = tinygltf::Value(extras);

	push(m_gltf_model.animations, anim);
}

void gltf_exporter::build_texture()
{
	const uint8_t* texture_data;
	const uint16_t* clut_data;

	texture_data = m_dw2_model.texture.data();
	clut_data =
		reinterpret_cast<const uint16_t*>(m_dw2_model.clut.data());

	image<uint8_t> texture_image(texture_data, 64, 256);
	image<uint16_t> clut_image(clut_data, 32, 32);

	clut_map cmap(256, 256, 4, 4);
	cmap.apply_model(m_dw2_model);

	std::vector<uint8_t> data;
	for (uint32_t j = 0; j < texture_image.height(); ++j)
	{
		for (uint32_t i = 0; i < texture_image.width(); ++i)
		{
			uint16_t t = texture_image.at(i, j);

			for (uint32_t k = 0; k < 2; ++k)
			{
				uint32_t clut = cmap.at(i * 2 + k, j);
				bool clut_stp = clut & DW2_CLUT_FLAG_STP;

				uint32_t color;
				if (clut == 0xffffffff)
				{
					color = 0;
				}
				else
				{
					uint16_t clut_x = (clut & 0x3f) << 4;
					uint16_t clut_y = (clut >> 6) & 0x3ff;

					assert(!clut_x || (clut_x == 16));
					assert((clut_y > 223) &&
					       (clut_y < 255));

					clut_x += (t >> (k * 4)) & 0xf;
					clut_y -= 224;

					color = clut_image.at(clut_x, clut_y);
				}

				uint8_t r = ((color >> 0) & 0x1f) << 3;
				uint8_t g = ((color >> 5) & 0x1f) << 3;
				uint8_t b = ((color >> 10) & 0x1f) << 3;
				bool stp = (color >> 15) & 1;
				uint8_t a = 0;

				if (!r && !g && !b)
				{
					a = stp ? 0xff : 0x00;
				}
				else
				{
					a = (clut_stp ? (0xff - stp * 0x80)
						      : 0xff);
				}

				data.push_back(r);
				data.push_back(g);
				data.push_back(b);
				data.push_back(a);
			}
		}
	}

	tinygltf::Image image;

	image.mimeType = "image/png";
	image.bits = 8;
	image.component = 4;
	image.pixel_type = TINYGLTF_COMPONENT_TYPE_UNSIGNED_BYTE;
	image.image = data;
	image.width = texture_image.width() * 2;
	image.height = texture_image.height();
	image.name = "texture";

	tinygltf::Sampler sampler;
	sampler.magFilter = TINYGLTF_TEXTURE_FILTER_NEAREST;
	sampler.minFilter = TINYGLTF_TEXTURE_FILTER_NEAREST;

	tinygltf::Texture tex;
	tex.source = push(m_gltf_model.images, image);
	tex.sampler = push(m_gltf_model.samplers, sampler);

	push(m_gltf_model.textures, tex);
}

tinygltf::Primitive gltf_exporter::build_primitives(
	const dw2_model_object& object, bool stp)
{
	tinygltf::Primitive prim;

	prim.mode = TINYGLTF_MODE_TRIANGLES;

	prim.material = build_material({stp, object.faces[0].mixture_rate});

	prim.attributes["POSITION"] = build_vertices(object, stp);
	prim.attributes["NORMAL"] = build_normals(object, stp);
	prim.attributes["TEXCOORD_0"] = build_texcoords0(object, stp);
	prim.attributes["TEXCOORD_1"] = build_texcoords1(object, stp);

	return prim;
}

int gltf_exporter::build_material(const material_mode& mode)
{
	std::map<material_mode, int>::const_iterator it;
	if ((it = m_materials.find(mode)) != m_materials.end())
	{
		return it->second;
	}

	tinygltf::Material mat;

	if (mode.stp)
	{
		mat.alphaMode = "BLEND";

		tinygltf::Value::Object extras;
		extras.emplace("blend_mode", mode.mixture_rate);
		mat.extras = tinygltf::Value(extras);
	}
	else
	{
		mat.alphaMode = "MASK";
		mat.alphaCutoff = 0.1f;
	}

	mat.pbrMetallicRoughness.baseColorFactor = {1.0f, 1.0f, 1.0f, 1.0f};
	mat.pbrMetallicRoughness.metallicFactor = 0.0f;
	mat.pbrMetallicRoughness.baseColorTexture.index = 0;

	return m_materials[mode] = push(m_gltf_model.materials, mat);
}

glm::vec3 fixed_to_real(const dw2_svec3& v, uint32_t decimal_bits)
{
	return {
		fixed_to_real<float>(v.x, decimal_bits),
		fixed_to_real<float>(-v.y, decimal_bits),
		fixed_to_real<float>(-v.z, decimal_bits),
	};
}

int gltf_exporter::build_vertices(const dw2_model_object& object, bool stp)
{
	std::vector<glm::vec3> data;

	for (const dw2_face& face : object.faces)
	{
		if (face.stp != stp)
		{
			continue;
		}

		dw2_svec3 sv;

		sv = object.vertices[face.vertex_indices[2]];
		data.push_back(fixed_to_real(sv, 0));
		sv = object.vertices[face.vertex_indices[1]];
		data.push_back(fixed_to_real(sv, 0));
		sv = object.vertices[face.vertex_indices[0]];
		data.push_back(fixed_to_real(sv, 0));
	}

	return build_accessor(data, TINYGLTF_COMPONENT_TYPE_FLOAT,
			      TINYGLTF_TYPE_VEC3,
			      TINYGLTF_TARGET_ARRAY_BUFFER);
}

int gltf_exporter::build_normals(const dw2_model_object& object, bool stp)
{
	std::vector<glm::vec3> data;

	for (const dw2_face& face : object.faces)
	{
		if (face.stp != stp)
		{
			continue;
		}

		dw2_svec3 sv;

		sv = object.normals[face.normal_indices[2]];
		data.push_back(fixed_to_real(sv, 12));
		sv = object.normals[face.normal_indices[1]];
		data.push_back(fixed_to_real(sv, 12));
		sv = object.normals[face.normal_indices[0]];
		data.push_back(fixed_to_real(sv, 12));
	}

	return build_accessor(data, TINYGLTF_COMPONENT_TYPE_FLOAT,
			      TINYGLTF_TYPE_VEC3,
			      TINYGLTF_TARGET_ARRAY_BUFFER);
}

int gltf_exporter::build_texcoords0(const dw2_model_object& object, bool stp)
{
	std::vector<glm::vec2> data;

	for (const dw2_face& face : object.faces)
	{
		if (face.stp != stp)
		{
			continue;
		}

		data.push_back({(face.uvs[2].x / 128.0f) + 0.0001f,
				(face.uvs[2].y / 256.0f) + 0.0001f});
		data.push_back({(face.uvs[1].x / 128.0f) + 0.0001f,
				(face.uvs[1].y / 256.0f) + 0.0001f});
		data.push_back({(face.uvs[0].x / 128.0f) + 0.0001f,
				(face.uvs[0].y / 256.0f) + 0.0001f});
	}

	return build_accessor(data, TINYGLTF_COMPONENT_TYPE_FLOAT,
			      TINYGLTF_TYPE_VEC2,
			      TINYGLTF_TARGET_ARRAY_BUFFER);
}

int gltf_exporter::build_texcoords1(const dw2_model_object& object, bool stp)
{
	std::vector<glm::vec2> data;

	for (const dw2_face& face : object.faces)
	{
		if (face.stp != stp)
		{
			continue;
		}

		uint16_t clut_x = (face.clut & 0x3f) << 4;
		uint16_t clut_y = ((face.clut & 0xffc0) >> 6);

		assert(!clut_x || (clut_x == 16));
		assert((clut_y > 223) && (clut_y < 255));

		float cx = (clut_x * 2 + 1) / 64.0f;
		float cy = ((clut_y - 224) * 2 + 1) / 64.0f;

		data.push_back({cx, cy});
		data.push_back({cx, cy});
		data.push_back({cx, cy});
	}

	return build_accessor(data, TINYGLTF_COMPONENT_TYPE_FLOAT,
			      TINYGLTF_TYPE_VEC2,
			      TINYGLTF_TARGET_ARRAY_BUFFER);
}

template <typename T>
T min_value(const T& a, const T& b)
{
	return std::min(a, b);
}

template <typename T>
T max_value(const T& a, const T& b)
{
	return std::max(a, b);
}

template <>
glm::vec2 min_value(const glm::vec2& a, const glm::vec2& b)
{
	return {std::min(a.x, b.x), std::min(a.y, b.y)};
}

template <>
glm::vec2 max_value(const glm::vec2& a, const glm::vec2& b)
{
	return {std::max(a.x, b.x), std::max(a.y, b.y)};
}

template <>
glm::vec3 min_value(const glm::vec3& a, const glm::vec3& b)
{
	return {std::min(a.x, b.x), std::min(a.y, b.y), std::min(a.z, b.z)};
}

template <>
glm::vec3 max_value(const glm::vec3& a, const glm::vec3& b)
{
	return {std::max(a.x, b.x), std::max(a.y, b.y), std::max(a.z, b.z)};
}

template <>
glm::quat min_value(const glm::quat& a, const glm::quat& b)
{
	return {std::min(a.w, b.w), std::min(a.x, b.x), std::min(a.y, b.y),
		std::min(a.z, b.z)};
}

template <>
glm::quat max_value(const glm::quat& a, const glm::quat& b)
{
	return {std::max(a.x, b.x), std::max(a.y, b.y), std::max(a.z, b.z),
		std::max(a.w, b.w)};
}

template <typename T>
void push_to_vector(std::vector<double>& vec, const T& val)
{
	vec.push_back(val);
}

template <>
void push_to_vector(std::vector<double>& vec, const glm::vec2& val)
{
	vec.push_back(val.x);
	vec.push_back(val.y);
}

template <>
void push_to_vector(std::vector<double>& vec, const glm::vec3& val)
{
	vec.push_back(val.x);
	vec.push_back(val.y);
	vec.push_back(val.z);
}

template <>
void push_to_vector(std::vector<double>& vec, const glm::quat& val)
{
	vec.push_back(val.x);
	vec.push_back(val.y);
	vec.push_back(val.z);
	vec.push_back(val.w);
}

template <typename T>
int gltf_exporter::build_accessor(const std::vector<T>& data,
				  int component_type, int type, int target)
{
	tinygltf::Buffer buffer;
	T min = data[0];
	T max = data[0];

	for (const T& val : data)
	{
		min = min_value(min, val);
		max = max_value(max, val);

		std::copy_n(reinterpret_cast<const uint8_t*>(&val),
			    sizeof(val), std::back_inserter(buffer.data));
	}

	int buffer_id = push(m_gltf_model.buffers, buffer);

	tinygltf::BufferView view;
	view.buffer = buffer_id;
	view.byteLength = buffer.data.size();
	view.byteOffset = 0;
	view.target = target;

	int view_id = push(m_gltf_model.bufferViews, view);

	tinygltf::Accessor accessor;
	accessor.bufferView = view_id;
	accessor.byteOffset = 0;
	accessor.componentType = component_type;
	accessor.count = data.size();
	accessor.type = type;
	push_to_vector(accessor.minValues, min);
	push_to_vector(accessor.maxValues, max);

	return push(m_gltf_model.accessors, accessor);
}
