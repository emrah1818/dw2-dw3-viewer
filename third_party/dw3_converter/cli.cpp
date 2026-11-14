// Headless DW3 -> GLB exporter with a dependency-free RGBA PNG writer.
#include "model.h"
#include "gltf.h"
#include "SDL3/SDL.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#include <algorithm>

bool SDL_CreateDirectory(const char *path) {
    std::filesystem::create_directories(path); return true;
}
SDL_Surface *SDL_CreateSurfaceFrom(int w, int h, int, void *pixels, int pitch) {
    return new SDL_Surface{w, h, pitch, pixels};
}
void SDL_DestroySurface(SDL_Surface *s) { delete s; }
static void be32(std::vector<uint8_t> &v, uint32_t x) {
    for (int shift = 24; shift >= 0; shift -= 8) v.push_back(uint8_t(x >> shift));
}
static void chunk(std::vector<uint8_t> &png, const char *type, const std::vector<uint8_t> &data) {
    be32(png, uint32_t(data.size()));
    size_t begin = png.size();
    png.insert(png.end(), type, type + 4);
    png.insert(png.end(), data.begin(), data.end());
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = begin; i < png.size(); i++) {
        crc ^= png[i];
        for (int bit = 0; bit < 8; bit++) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1)));
    }
    be32(png, crc ^ 0xFFFFFFFF);
}
bool SDL_SavePNG(SDL_Surface *s, const char *path) {
    if (!s || s->w <= 0 || s->h <= 0 || s->w > 4096 || s->h > 4096) return false;
    std::vector<uint8_t> raw;
    for (int y = 0; y < s->h; y++) {
        raw.push_back(0);
        auto p = static_cast<uint8_t *>(s->pixels) + y * s->pitch;
        raw.insert(raw.end(), p, p + s->w * 4);
    }
    std::vector<uint8_t> z = {0x78, 0x01};
    for (size_t pos = 0; pos < raw.size();) {
        uint16_t n = uint16_t(std::min(size_t(65535), raw.size() - pos));
        z.push_back(pos + n == raw.size() ? 1 : 0);
        z.push_back(n & 255); z.push_back(n >> 8);
        z.push_back((~n) & 255); z.push_back((~n) >> 8);
        z.insert(z.end(), raw.begin() + pos, raw.begin() + pos + n); pos += n;
    }
    uint32_t a = 1, b = 0;
    for (auto c : raw) { a = (a + c) % 65521; b = (b + a) % 65521; }
    be32(z, (b << 16) | a);
    std::vector<uint8_t> png = {137, 80, 78, 71, 13, 10, 26, 10}, ihdr;
    be32(ihdr, s->w); be32(ihdr, s->h);
    ihdr.insert(ihdr.end(), {8, 6, 0, 0, 0});
    chunk(png, "IHDR", ihdr); chunk(png, "IDAT", z); chunk(png, "IEND", {});
    std::ofstream out(path, std::ios::binary);
    out.write(reinterpret_cast<const char *>(png.data()), png.size());
    return bool(out);
}
int main(int argc, char **argv) {
    if (argc != 3) { std::cerr << "Usage: dw3_converter MODEL.BIN OUTPUT_DIR\n"; return 2; }
    try {
        std::ifstream in(argv[1], std::ios::binary);
        if (!in) return 2;
        std::vector<uint8_t> bytes(std::istreambuf_iterator<char>(in), {});
        if (bytes.size() < 8 || bytes.size() > 32 * 1024 * 1024) return 2;
        Model model;
        if (!model.load("DW3 model", std::move(bytes), nullptr, -1, -1)) {
            std::cerr << model.error << '\n'; return 3;
        }
        std::string error;
        if (!export_gltf(model, argv[2], "model", error)) { std::cerr << error; return 4; }
        std::cout << model.bones.size() << " bones, " << model.meshes.size() << " meshes, " << model.motions.size() << " motions\n";
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what(); return 5; }
}
